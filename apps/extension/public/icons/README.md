# Icons

Source `icon.svg` — run `pnpm icons:build` (script rasterizes to 16/32/48/128 PNGs using sharp).

The build currently references PNG paths in `manifest.config.ts`; a pre-build step must produce these files. For the first packaging, run:

```
pnpm --filter @meetingmate/extension dlx sharp-cli --input public/icons/icon.svg --output public/icons/icon-128.png --format png --height 128
pnpm --filter @meetingmate/extension dlx sharp-cli --input public/icons/icon.svg --output public/icons/icon-48.png --format png --height 48
pnpm --filter @meetingmate/extension dlx sharp-cli --input public/icons/icon.svg --output public/icons/icon-32.png --format png --height 32
pnpm --filter @meetingmate/extension dlx sharp-cli --input public/icons/icon.svg --output public/icons/icon-16.png --format png --height 16
```

This keeps binary PNGs out of source control while still producing a Chrome-Web-Store-compliant bundle.
