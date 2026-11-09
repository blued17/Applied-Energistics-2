# ===== Pinned crafting row (client side) =====
base = 'src/main/java/appeng/client/gui/me/'

def edit(path, pairs):
    s = open(base + path).read()
    if 'PinnedStacks' in s:
        return
    for old, new, count in pairs:
        assert s.count(old) == count, 'anchor not found %d time(s) in %s: %s' % (count, path, old)
        s = s.replace(old, new)
    open(base + path, 'w').write(s)

open(base + 'common/PinnedStacks.java', 'w').write('''package appeng.client.gui.me.common;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

import appeng.api.storage.data.IAEStack;

/**
 * Client-side list of stacks that are pinned to the first row of the terminal while they are being crafted.
 */
public final class PinnedStacks {

    public static final int MAX_PINNED = 9;
    private static final long MAX_AGE_MS = 30L * 60L * 1000L;

    private static final List<Pin> PINS = new ArrayList<>();
    private static IAEStack<?> pending;

    private static final class Pin {
        final IAEStack<?> stack;
        long since = System.currentTimeMillis();
        boolean canPrune;

        Pin(IAEStack<?> stack) {
            this.stack = stack;
        }
    }

    private PinnedStacks() {
    }

    public static boolean isEmpty() {
        return PINS.isEmpty();
    }

    public static boolean isPinned(IAEStack<?> stack) {
        return find(stack) != null;
    }

    public static long getPinTime(IAEStack<?> stack) {
        Pin pin = find(stack);
        return pin != null ? pin.since : Long.MAX_VALUE;
    }

    private static Pin find(IAEStack<?> stack) {
        if (stack == null) {
            return null;
        }
        for (Pin pin : PINS) {
            if (pin.stack.equals(stack)) {
                return pin;
            }
        }
        return null;
    }

    public static void pin(IAEStack<?> stack) {
        if (stack == null) {
            return;
        }
        Pin existing = find(stack);
        if (existing != null) {
            existing.since = System.currentTimeMillis();
            existing.canPrune = false;
            return;
        }
        PINS.add(new Pin(stack.copy()));
        while (PINS.size() > MAX_PINNED) {
            Pin oldest = PINS.get(0);
            for (Pin pin : PINS) {
                if (pin.since < oldest.since) {
                    oldest = pin;
                }
            }
            PINS.remove(oldest);
        }
    }

    /**
     * Remembers what the player asked to craft in the terminal.
     */
    public static void setPendingRequest(IAEStack<?> stack) {
        if (stack == null) {
            pending = null;
        } else {
            pending = stack.copy();
        }
    }

    /**
     * Called when a crafting job is started: pins what the player last asked to craft.
     */
    public static void pinPendingRequest() {
        if (pending != null) {
            pin(pending);
            pending = null;
        }
    }

    /**
     * Flags all pins for removal the next time a terminal is opened.
     */
    public static void markPrunable() {
        for (Pin pin : PINS) {
            pin.canPrune = true;
        }
    }

    public static void prune() {
        long now = System.currentTimeMillis();
        Iterator<Pin> it = PINS.iterator();
        while (it.hasNext()) {
            Pin pin = it.next();
            if (pin.canPrune || now - pin.since > MAX_AGE_MS) {
                it.remove();
            }
        }
    }

}
''')

edit('common/Repo.java', [
    ('    private final ArrayList<GridInventoryEntry<T>> view = new ArrayList<>();\n',
     '    private final ArrayList<GridInventoryEntry<T>> view = new ArrayList<>();\n'
     '    private final ArrayList<GridInventoryEntry<T>> pinnedRow = new ArrayList<>();\n', 1),
    ('        this.view.sort(Comparator.comparing(GridInventoryEntry::getStack, getComparator(sortOrder, sortDir)));\n',
     '        this.view.sort(Comparator.comparing(GridInventoryEntry::getStack, getComparator(sortOrder, sortDir)));\n'
     '\n'
     '        // Pinned entries ignore the search and are shown in a fixed first row\n'
     '        this.pinnedRow.clear();\n'
     '        if (!PinnedStacks.isEmpty()) {\n'
     '            ArrayList<GridInventoryEntry<T>> found = new ArrayList<>();\n'
     '            for (GridInventoryEntry<T> entry : this.entries.values()) {\n'
     '                if (PinnedStacks.isPinned(entry.getStack())\n'
     '                        && (this.partitionList == null || this.partitionList.isListed(entry.getStack()))) {\n'
     '                    found.add(entry);\n'
     '                }\n'
     '            }\n'
     '            found.sort((a, b) -> Long.compare(PinnedStacks.getPinTime(a.getStack()),\n'
     '                    PinnedStacks.getPinTime(b.getStack())));\n'
     '            for (GridInventoryEntry<T> entry : found) {\n'
     '                if (this.pinnedRow.size() < this.rowSize) {\n'
     '                    this.pinnedRow.add(entry);\n'
     '                }\n'
     '            }\n'
     '            this.view.removeAll(this.pinnedRow);\n'
     '        }\n', 1),
    ('        idx += this.src.getCurrentScroll() * this.rowSize;\n',
     '        if (!this.pinnedRow.isEmpty()) {\n'
     '            if (idx < this.rowSize) {\n'
     '                return idx < this.pinnedRow.size() ? this.pinnedRow.get(idx) : null;\n'
     '            }\n'
     '            idx -= this.rowSize;\n'
     '        }\n'
     '        idx += this.src.getCurrentScroll() * this.rowSize;\n', 1),
    ('        return this.view.size();\n',
     '        return this.view.size() + (this.pinnedRow.isEmpty() ? 0 : this.rowSize);\n', 1),
    ('        this.entries.clear();\n        this.view.clear();\n',
     '        this.entries.clear();\n        this.view.clear();\n        this.pinnedRow.clear();\n', 1),
    ('    public final boolean hasPower() {',
     '    public final boolean hasPinnedRow() {\n        return !this.pinnedRow.isEmpty();\n    }\n\n    public final int getPinnedCount() {\n        return this.pinnedRow.size();\n    }\n\n    public final boolean hasPower() {', 1),
])

edit('common/MEMonitorableScreen.java', [
    ('        getMinecraft().keyboardListener.enableRepeatEvents(true);\n',
     '        PinnedStacks.prune();\n        getMinecraft().keyboardListener.enableRepeatEvents(true);\n', 1),
    ('        memoryText = this.searchField.getText();\n',
     '        memoryText = this.searchField.getText();\n'
     '        if (this.container.activeCraftingJobs == 0) {\n'
     '            PinnedStacks.markPrunable();\n'
     '        }\n', 1),
    ('        style.getBottom().dest(offsetX, y).blit(matrixStack, getBlitOffset());\n',
     '        style.getBottom().dest(offsetX, y).blit(matrixStack, getBlitOffset());\n'
     '\n'
     '        // Decoration for the pinned row\n'
     '        if (this.repo.hasPinnedRow()) {\n'
     '            int pinX = offsetX + 8;\n'
     '            int pinY = offsetY + style.getHeader().getSrcHeight();\n'
     '            fill(matrixStack, pinX, pinY, pinX + 9 * 18, pinY + 18, 0x408CB4FF);\n'
     '            for (int col = this.repo.getPinnedCount(); col < 9; col++) {\n'
     '                drawPinGlyph(matrixStack, pinX + col * 18 + 5, pinY + 6);\n'
     '            }\n'
     '        }\n', 1),
    ('    // TODO This is incorrectly named in MCP, it\'s renderSlot, essentially\n',
     '    private void drawPinGlyph(MatrixStack matrices, int x, int y) {\n'
     '        int[][] runs = { { 0, 5, 9 }, { 1, 4, 8 }, { 2, 3, 7 }, { 3, 2, 6 }, { 4, 1, 3 }, { 5, 0, 2 } };\n'
     '        for (int[] run : runs) {\n'
     '            fill(matrices, x + run[1], y + run[0], x + run[2], y + run[0] + 1, 0xFF6E7191);\n'
     '        }\n'
     '    }\n'
     '\n'
     '    // TODO This is incorrectly named in MCP, it\'s renderSlot, essentially\n', 1),
    ('                if (entry != null) {\n                    try {\n                        renderGridInventoryEntry(matrices, s.xPos, s.yPos, entry);\n',
     '                if (entry != null) {\n'
     '                    // Rainbow square around pinned entries while crafting jobs are running\n'
     '                    if (this.container.activeCraftingJobs > 0 && PinnedStacks.isPinned(entry.getStack())) {\n'
     '                        net.minecraft.client.renderer.texture.TextureAtlasSprite lights = getMinecraft()\n'
     '                                .getAtlasSpriteGetter(net.minecraft.inventory.container.PlayerContainer.LOCATION_BLOCKS_TEXTURE)\n'
     '                                .apply(AppEng.makeId("block/molecular_assembler_lights"));\n'
     '                        getMinecraft().getTextureManager()\n'
     '                                .bindTexture(net.minecraft.inventory.container.PlayerContainer.LOCATION_BLOCKS_TEXTURE);\n'
     '                        com.mojang.blaze3d.systems.RenderSystem.enableBlend();\n'
     '                        com.mojang.blaze3d.systems.RenderSystem.defaultBlendFunc();\n'
     '                        blit(matrices, s.xPos - 1, s.yPos - 1, getBlitOffset(), 18, 18, lights);\n'
     '                    }\n'
     '                    try {\n                        renderGridInventoryEntry(matrices, s.xPos, s.yPos, entry);\n', 1),
])

edit('items/ItemTerminalScreen.java', [
    ('package appeng.client.gui.me.items;\n',
     'package appeng.client.gui.me.items;\n\nimport appeng.client.gui.me.common.PinnedStacks;\n', 1),
    ('container.handleInteraction(serial, InventoryAction.AUTO_CRAFT);',
     'PinnedStacks.setPendingRequest(entry.getStack());\n                        container.handleInteraction(serial, InventoryAction.AUTO_CRAFT);', 2),
])

edit('crafting/CraftConfirmScreen.java', [
    ('package appeng.client.gui.me.crafting;\n',
     'package appeng.client.gui.me.crafting;\n\nimport appeng.client.gui.me.common.PinnedStacks;\n', 1),
    ('        NetworkHandler.instance().sendToServer(new ConfigValuePacket("Terminal.Start", "Start"));',
     '        PinnedStacks.pinPendingRequest();\n        NetworkHandler.instance().sendToServer(new ConfigValuePacket("Terminal.Start", "Start"));', 1),
])

edit('crafting/CraftAmountScreen.java', [
    ('package appeng.client.gui.me.crafting;\n',
     'package appeng.client.gui.me.crafting;\n\nimport appeng.client.gui.me.common.PinnedStacks;\n', 1),
    ('        container.confirm(amount, hasShiftDown());',
     '        if (hasShiftDown()) {\n            PinnedStacks.pinPendingRequest();\n        }\n        container.confirm(amount, hasShiftDown());', 1),
])
print('pins applied')
