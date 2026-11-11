from PIL import Image
D = 'src/main/resources/assets/appliedenergistics2/textures/guis/'
sel = Image.open(D + 'cpu_selector.png').convert('RGBA')
states = Image.open('/tmp/states.png').convert('RGBA')
T = 1.0
def dark(img):
    px = img.load()
    for yy in range(img.height):
        for xx in range(img.width):
            r, g, b, a = px[xx, yy]
            px[xx, yy] = (int(r * T), int(g * T), int(b * T), a)
    return img
for (sx, sy), (dx, dy) in [((208, 224), (100, 50)), ((208, 234), (112, 50)), ((208, 244), (124, 50))]:
    sel.paste(dark(states.crop((sx, sy, sx + 10, sy + 10))), (dx, dy))
sel.save(D + 'cpu_selector.png')
print('icons merged')
