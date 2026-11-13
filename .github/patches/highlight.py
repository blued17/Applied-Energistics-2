# ===== Blue slot highlight when the mouse is over a slot (like in newer AE2 versions) =====
path = 'src/main/java/appeng/client/gui/AEBaseScreen.java'
s = open(path).read()
if 'drawSlotHighlightBorder' not in s:
    def rep(old, new):
        global s
        assert s.count(old) == 1, 'anchor not found exactly once: ' + old[:80]
        s = s.replace(old, new)

    # border around the hovered slot, drawn after the (now blue) vanilla fill
    rep('    protected final void drawGuiContainerForegroundLayer(MatrixStack matrixStack, final int x, final int y) {\n'
        '        final int ox = this.guiLeft;\n'
        '        final int oy = this.guiTop;\n',
        '    protected final void drawGuiContainerForegroundLayer(MatrixStack matrixStack, final int x, final int y) {\n'
        '        final int ox = this.guiLeft;\n'
        '        final int oy = this.guiTop;\n'
        '\n'
        '        if (this.hoveredSlot != null && this.hoveredSlot.isEnabled()) {\n'
        '            drawSlotHighlightBorder(matrixStack, this.hoveredSlot.xPos, this.hoveredSlot.yPos, 16, 16);\n'
        '        }\n')

    # custom (non-vanilla) slots get the same highlight
    rep('                this.fillGradient(matrixStack, left, top, right, bottom, -2130706433, -2130706433);\n',
        '                this.fillGradient(matrixStack, left, top, right, bottom, 0x669CD3FF, 0x669CD3FF);\n'
        '                drawSlotHighlightBorder(matrixStack, left, top, right - left, bottom - top);\n')

    rep('    private void drawTooltip(MatrixStack matrixStack, Tooltip tooltip, int mouseX, int mouseY) {\n',
        '''    /**
     * The color of the highlight of the slot under the mouse. This replaces the white highlight of Vanilla.
     */
    public int getSlotColor(int index) {
        return 0x669CD3FF;
    }

    private void drawSlotHighlightBorder(MatrixStack matrixStack, int x, int y, int w, int h) {
        hLine(matrixStack, x, x + w, y - 1, 0xFFDAFFFF);
        hLine(matrixStack, x - 1, x + w, y + h, 0xFFDAFFFF);
        vLine(matrixStack, x - 1, y - 2, y + h, 0xFFDAFFFF);
        vLine(matrixStack, x + w, y - 2, y + h, 0xFFDAFFFF);
    }

    private void drawTooltip(MatrixStack matrixStack, Tooltip tooltip, int mouseX, int mouseY) {
''')
    open(path, 'w').write(s)
print('highlight applied')
