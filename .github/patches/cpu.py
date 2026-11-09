import re
# ---------- 1. version + cluster getter + lang + status json (idempotent) ----------
p = 'src/main/java/appeng/me/cluster/implementations/CraftingCPUCluster.java'
s = open(p).read()
if 'getFinalOutput' not in s:
    s = s.replace("    public long getElapsedTime() {",
        "    public IAEItemStack getFinalOutput() {\n        return this.finalOutput != null ? this.finalOutput.copy() : null;\n    }\n\n    public long getElapsedTime() {", 1)
    assert 'getFinalOutput' in s
    open(p, 'w').write(s)

p = 'src/main/resources/assets/appliedenergistics2/lang/en_us.json'
s = open(p).read().rstrip()
if 'CpuStatusStorage' not in s:
    body = s[:-1].rstrip()
    add = ''',
  "gui.appliedenergistics2.CraftingCPUs": "Crafting CPUs",
  "gui.appliedenergistics2.CpuStatusCoProcessor": "%s Co-Processor",
  "gui.appliedenergistics2.CpuStatusCoProcessors": "%s Co-Processors",
  "gui.appliedenergistics2.CpuStatusStorage": "%s Storage",
  "gui.appliedenergistics2.CpuStatusCrafting": "Crafting: %s",
  "gui.appliedenergistics2.CpuStatusCraftedIn": "%s done after %s"
}
'''
    open(p, 'w').write(body + add)

p = 'src/main/resources/assets/appliedenergistics2/screens/crafting_status.json'
open(p, 'w').write('''{
  "$schema": "schema.json",
  "includes": ["crafting_cpu.json"],
  "widgets": {
    "back": {"left": 213, "top": -4, "hideEdge": true},
    "selectCpuList": {"left": -88, "top": 0, "width": 94, "height": 164},
    "selectCpuScrollbar": {"left": -11, "top": 19, "width": 12, "height": 137}
  }
}
''')

# ---------- 2. widget: icons from the selector texture + explicit button colors ----------
p = 'src/main/java/appeng/client/gui/widgets/CPUSelectionList.java'
s = open(p).read()
if 'drawButton(' not in s:
    def rep(old, new):
        global s
        assert s.count(old) == 1, 'patch anchor not found exactly once: ' + old
        s = s.replace(old, new)
    rep('ICON_TEXTURE = "guis/cpu_icons.png"', 'ICON_TEXTURE = "guis/cpu_selector.png"')
    rep('icon(208, 224)', 'icon(100, 50)')
    rep('icon(208, 234)', 'icon(112, 50)')
    rep('icon(208, 244)', 'icon(124, 50)')
    rep('button(selected).dest(x, y).blit(matrices, zIndex);', 'drawButton(matrices, x, y, selected);')
    rep('selected ? PROGRESS_COLOR_SELECTED : PROGRESS_COLOR', 'selected ? 0xFF3A78B8 : 0xFF9CD3FF')
    rep('    private void drawScaledText(', '''    private static void drawButton(MatrixStack matrices, int x, int y, boolean selected) {
        int shade = selected ? 0xFF708CBA : 0xFF4D4D67;
        int light = selected ? 0xFFDAFFFF : 0xFF9A9FB4;
        int body = selected ? 0xFF9CD3FF : 0xFF878FA5;
        AbstractGui.fill(matrices, x, y, x + BUTTON_WIDTH, y + BUTTON_HEIGHT, shade);
        AbstractGui.fill(matrices, x, y, x + BUTTON_WIDTH - 1, y + BUTTON_HEIGHT - 1, light);
        AbstractGui.fill(matrices, x + 1, y + 1, x + BUTTON_WIDTH - 1, y + BUTTON_HEIGHT - 1, body);
    }

    private void drawScaledText(''')
    open(p, 'w').write(s)
