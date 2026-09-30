# 이미지 제작 기록

ChatGPT/Codex 내장 ImageGen으로 새 픽셀 아트 캐릭터와 동작 시트를 생성했습니다.
사용자가 제공한 소닉 시트는 다양한 포즈를 담은 스프라이트 시트의 구성 참고로,
검사 시트는 어두운 의상, 포니테일, 검을 쓰는 캐릭터의 스타일 참고로 사용했습니다.
첨부 이미지의 픽셀을 복사해 최종 자산에 넣지는 않았습니다.

처음 생성한 시트는 공격 프레임 간 간격이 좁아 최종 자산에서 제외했습니다.
최종 생성 결과는 1774×887 RGBA PNG이며, 요청한 2048×1024와 실제 해상도는 달랐습니다.
`build_atlas.py`는 실제 크기를 읽고 행별 투명 간격에서 프레임을 나눈 뒤,
선택한 26포즈를 픽셀/알파 값을 그대로 유지하여 1209×798 atlas에 다시 배치합니다.
실제 실행 시트는 `assets/sprite_atlas.png`이고 최종 원본은 `assets/generated_source.png`입니다.

선택한 프레임(0부터 시작): Walk [0,1,2,4,5,6], Run [0,1,2,3,4,5,6,7],
Jump [0,1,2,4,5,6,7], Attack [0,2,4,6,7].
이 선택으로 주요 동작 단계를 유지하며 동작별 프레임 수가 다르도록 구성했습니다.
원본 크롭 좌표는 `assets/packing_provenance.json`에서 확인할 수 있습니다.

## 최종 생성 프롬프트

transparent_background: true

```text
Create a NEW production sprite sheet, exactly 2048x1024 pixels, 8 equal columns and 4 equal rows. Every cell is 256x256 pixels. 32 isolated sprites TOTAL. Use the extra-wide 256-pixel cells so every blade fits without touching any neighboring sprite. Transparent background, no ambient glow or background color. Subject: original 16-bit pixel art side-view young samurai, dark navy robe, blue-black high ponytail, peach hands and face, red-orange shoes, thin silver katana. All face RIGHT, consistent identity, outfit, and anatomical scale. Each sprite body approximately 150 pixels tall. Every entire sprite must fit inside the centered 200x200 region of its cell, leaving AT LEAST 28 empty pixels along ALL FOUR EDGES. No shared props across cells; all swords belong to only one sprite. Row 1 exactly 8 walking-loop poses alternating foot steps. Row 2 exactly 8 running-loop poses, forward lean, alternating legs and arms. Row 3 exactly 8 jumping phases: crouch, takeoff, rise, apex tuck, apex extension, fall, land, stand. Row 4 exactly 8 sword-attack phases: ready, unsheathe, raise backward, overhead windup, forward slash, forward extension, retract, return to ready. Make the sword SHORT, maximum 70 pixels, and the cyan slash arc SMALL to guarantee whole attack figures occupy at most 200x200 pixels. Sword tips must never leave their cells. Precise pixel sprites with flat color fills and crisp dark outlines. No text, labels, grid lines, shadows, haze, scenery, or watermark.
```
