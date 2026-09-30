"""Behavior checks for the rubric; no display or third-party test runner needed."""
import math
from pathlib import Path
import struct
import sys
import unittest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
import animation_viewer as viewer


class RubricTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.animations = viewer.load_manifest()

    def test_four_actions_with_different_frame_counts(self):
        self.assertEqual([a.name for a in self.animations], ['walk', 'run', 'jump', 'attack'])
        self.assertEqual([len(a.frames) for a in self.animations], [6, 8, 7, 5])

    def test_png_matches_metadata_and_all_rectangles_fit(self):
        image = APP / 'assets' / self.data['image']
        header = image.read_bytes()[:24]
        self.assertEqual(header[:8], b'\x89PNG\r\n\x1a\n')
        self.assertEqual(list(struct.unpack('>II', header[16:24])), self.data['size'])
        viewer.validate_manifest(self.data, self.animations)
        frames = [f for a in self.animations for f in a.frames]
        self.assertGreater(len({(f.width, f.height) for f in frames}), 15)
        for i, a in enumerate(frames):
            for b in frames[i + 1:]:
                overlap = (a.x < b.x + b.width and b.x < a.x + a.width and
                           a.y < b.y + b.height and b.y < a.y + a.height)
                self.assertFalse(overlap, 'Packed frames must never overlap')

    def test_five_full_cycles_then_one_second_rest(self):
        for index, action in enumerate(self.animations):
            player = viewer.Playback(self.animations)
            player.animation_index = index
            for repeat in range(5):
                player.elapsed = repeat * action.cycle_seconds
                self.assertFalse(player.resting)
                self.assertEqual(player.completed_repeats, repeat)
                self.assertEqual(player.frame_index, 0)
                for frame_index in range(len(action.frames)):
                    player.elapsed = repeat * action.cycle_seconds + (frame_index + 0.5) * action.frame_seconds
                    self.assertEqual(player.frame_index, frame_index)
            player.elapsed = viewer.play_seconds(action)
            self.assertTrue(player.resting)
            self.assertEqual(player.completed_repeats, 5)
            self.assertEqual(player.frame_index, len(action.frames) - 1)
            player.update(0.999)
            self.assertEqual(player.animation_index, index)
            self.assertEqual(player.frame_index, len(action.frames) - 1)
            player.update(0.001)
            self.assertEqual(player.animation_index, (index + 1) % len(self.animations))
            self.assertAlmostEqual(player.elapsed, 0)

    def test_sequence_wraps_and_preserves_time_remainder(self):
        player = viewer.Playback(self.animations)
        period = sum(viewer.play_seconds(a) + viewer.REST_SECONDS for a in self.animations)
        player.update(period * 10 + 0.25)
        self.assertEqual(player.animation_index, 0)
        self.assertAlmostEqual(player.elapsed, 0.25)

    def test_small_time_steps_match_a_large_time_step(self):
        small = viewer.Playback(self.animations)
        large = viewer.Playback(self.animations)
        for _ in range(5000):
            small.update(1 / 60)
        large.update(5000 / 60)
        self.assertEqual(small.animation_index, large.animation_index)
        self.assertEqual(small.frame_index, large.frame_index)
        self.assertAlmostEqual(small.elapsed, large.elapsed)

    def test_every_character_is_large_and_inside_the_stage(self):
        player = viewer.Playback(self.animations)
        for index, action in enumerate(self.animations):
            player.animation_index = index
            for frame_index, frame in enumerate(action.frames):
                player.elapsed = (frame_index + 0.5) * action.frame_seconds
                scale = viewer.display_scale(frame)
                self.assertGreaterEqual(frame.height * scale, viewer.WINDOW_HEIGHT * 0.5)
                x, baseline = viewer.character_position(player)
                left = x - frame.pivot_x * scale
                self.assertGreaterEqual(left, 24)
                self.assertLessEqual(left + frame.width * scale, viewer.WINDOW_WIDTH - 24)
                self.assertGreaterEqual(baseline, viewer.FLOOR_Y)
                self.assertLessEqual(baseline + frame.height * scale, viewer.WINDOW_HEIGHT - 122 + 1e-6)

    def test_rightward_motion_speed_jump_and_attack_lunge(self):
        walk = viewer.Playback(self.animations)
        run = viewer.Playback(self.animations)
        run.animation_index = 1
        start_x = viewer.character_position(walk)[0]
        walk.update(.25)
        run.update(.25)
        self.assertGreater(viewer.character_position(walk)[0], start_x)
        self.assertGreater(viewer.character_position(run)[0], viewer.character_position(walk)[0])
        jump = viewer.Playback(self.animations)
        jump.animation_index = 2
        jump.elapsed = jump.animation.cycle_seconds * 3 / 7
        self.assertGreater(viewer.character_position(jump)[1], viewer.FLOOR_Y + 60)
        jump.elapsed = jump.animation.cycle_seconds * 6 / 7
        self.assertEqual(viewer.character_position(jump)[1], viewer.FLOOR_Y)
        attack = viewer.Playback(self.animations)
        attack.animation_index = 3
        attack.elapsed = attack.animation.cycle_seconds * .2
        self.assertEqual(viewer.character_position(attack)[0], start_x)
        attack.elapsed = attack.animation.cycle_seconds * .7
        self.assertGreater(viewer.character_position(attack)[0], start_x + 40)

    def test_motion_stays_inside_canvas_and_freezes_during_rest(self):
        player = viewer.Playback(self.animations)
        period = sum(viewer.play_seconds(a) + viewer.REST_SECONDS for a in self.animations)
        for _ in range(math.ceil(period * 60) * 2):
            x, y = viewer.character_position(player)
            frame = player.animation.frames[player.frame_index]
            scale = viewer.display_scale(frame)
            self.assertGreaterEqual(x - frame.pivot_x * scale, 24 - 1e-6)
            self.assertLessEqual(x + (frame.width - frame.pivot_x) * scale, viewer.WINDOW_WIDTH - 24 + 1e-6)
            self.assertGreaterEqual(y, viewer.FLOOR_Y)
            self.assertLessEqual(y + frame.height * scale, viewer.WINDOW_HEIGHT - 122 + 1e-6)
            player.update(1 / 60)
        for index, action in enumerate(self.animations):
            player.animation_index = index
            player.elapsed = viewer.play_seconds(action)
            position = viewer.character_position(player)
            player.update(.5)
            self.assertEqual(viewer.character_position(player), position)
        self.assertEqual(viewer.character_position(viewer.Playback(self.animations)),
                         (viewer.movement_bounds(self.animations)[0], viewer.FLOOR_Y))

    def test_clip_coordinates_use_bottom_origin(self):
        frame = viewer.Frame(20, 30, 60, 80, 30, 80)
        self.assertEqual(viewer.clip_rectangle(frame, 500), (20, 390, 60, 80))

    def test_invalid_times_and_frame_bounds_are_rejected(self):
        player = viewer.Playback(self.animations)
        for value in [-1, math.nan, math.inf]:
            with self.assertRaises(ValueError):
                player.update(value)
        action = viewer.Animation('bad', 'Bad', 0.1, (viewer.Frame(-1, 0, 10, 10, 5, 10),))
        with self.assertRaises(ValueError):
            viewer.validate_manifest(self.data, (action, *self.animations[1:]))


if __name__ == '__main__':
    unittest.main()
