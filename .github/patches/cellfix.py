# ===== Cell preview: use blank space as the placeholder so the tooltip is wide enough for the icons =====
path = 'src/main/java/appeng/client/render/CellPreviewTooltip.java'
s = open(path).read()
old = 'private static final String MARKER = "\\u200B";'
if old in s:
    s = s.replace(old, 'private static final String MARKER = "' + ' ' * 24 + '";')
    open(path, 'w').write(s)
elif 'MARKER = "' + ' ' * 24 + '"' not in s:
    raise SystemExit('marker constant not found')
print('cell preview placeholder updated')
