# Оформление «Рядом»

`src/assets/journey.webp` — оригинальная декоративная иллюстрация, созданная встроенным инструментом imagegen для этого интерфейса. Это вымышленный пейзаж, а не фотография Коломны или другого реального города. Используется в онбординге и на главной. Исходный PNG 1536×1024 конвертирован в WebP (quality 86) без изменения содержания; итог около 380 КБ. В UI иллюстративный характер обозначен.

## Финальный промпт

Use case: stylized-concept. Asset type: original hero illustration for a premium mobile app about short local trips through Russia, used as a full-bleed onboarding cover and a travel inspiration card. Create one high-quality editorial 3D paper-cut / tactile clay miniature landscape illustration, landscape aspect ratio 3:2. A beautiful winding turquoise-blue river leads from the foreground across a green countryside to a small charming historic Russian town with a modest white church with a tiny blue onion dome, warm red brick tower, pale pink and ochre houses; rounded trees, gently rolling hills, a little cream road and a small blue train, clear soft sky. The scene is fictional and stylized, not an accurate depiction of any real city. Modern high-end travel brand art direction, sunny airy spring/summer daylight, soft shadows, subtle matte tactile surfaces, pleasing quiet detail. Pale warm ivory, soft sage greenery, cobalt blue details, restrained terracotta. Balanced composition with key structures and river in the middle, usable for cropping on mobile. Fill the entire canvas, no frames, no UI, no text, no logos, no watermarks, no people, not a flat SVG, not a screenshot. The image must feel inviting and sophisticated, not childish.

## Остальные элементы

- Manrope Variable поставляется локально через `@fontsource-variable/manrope`, без запроса к Google Fonts.
- Иконки — `lucide-react`, движение — `motion/react`; версии закреплены в package-lock.json.
- Миниатюры настроений и оформление загрузки — CSS, логотип — текст и иконка компаса.
- `prefers-reduced-motion` отключает CSS-анимации; MotionConfig учитывает пользовательскую настройку уменьшения движения.
