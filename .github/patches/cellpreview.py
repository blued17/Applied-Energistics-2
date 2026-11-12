# ===== Show the stored items of a cell in its tooltip (like newer AE2 versions) =====
open('src/main/java/appeng/client/render/CellPreviewTooltip.java', 'w').write('''package appeng.client.render;

import java.util.ArrayList;
import java.util.List;

import com.mojang.blaze3d.systems.RenderSystem;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.FontRenderer;
import net.minecraft.client.renderer.ItemRenderer;
import net.minecraft.item.ItemStack;
import net.minecraft.util.text.ITextComponent;
import net.minecraft.util.text.ITextProperties;
import net.minecraft.util.text.StringTextComponent;
import net.minecraftforge.client.event.RenderTooltipEvent;

import appeng.api.storage.ICellInventoryHandler;
import appeng.api.storage.data.IAEStack;
import appeng.api.storage.data.IItemList;
import appeng.util.ReadableNumberConverter;

/**
 * Draws icons of the most stored stacks of a cell inside its tooltip.
 */
public final class CellPreviewTooltip {

    private static final String MARKER = "\\u200B";
    private static final int MAX_ICONS = 5;

    private static final List<ItemStack> ICONS = new ArrayList<>();
    private static final List<Long> COUNTS = new ArrayList<>();
    private static boolean hasMore;

    private CellPreviewTooltip() {
    }

    /**
     * Called while the tooltip lines are built. Remembers what to draw and reserves space in the tooltip.
     */
    public static <T extends IAEStack<T>> void addPreview(ICellInventoryHandler<T> handler,
            List<ITextComponent> lines) {
        ICONS.clear();
        COUNTS.clear();
        hasMore = false;
        if (handler == null) {
            return;
        }

        final IItemList<T> list = handler.getAvailableItems(handler.getChannel().createList());
        final List<T> stacks = new ArrayList<>();
        for (final T stack : list) {
            stacks.add(stack);
        }
        if (stacks.isEmpty()) {
            return;
        }
        stacks.sort((a, b) -> Long.compare(b.getStackSize(), a.getStackSize()));

        for (int i = 0; i < Math.min(MAX_ICONS, stacks.size()); i++) {
            final ItemStack icon = stacks.get(i).asItemStackRepresentation();
            if (!icon.isEmpty()) {
                ICONS.add(icon);
                COUNTS.add(stacks.get(i).getStackSize());
            }
        }
        hasMore = stacks.size() > MAX_ICONS;
        if (ICONS.isEmpty()) {
            return;
        }

        // Two empty lines give room for the 16 pixel high icons
        lines.add(new StringTextComponent(MARKER));
        lines.add(new StringTextComponent(MARKER));
    }

    public static void onPostText(RenderTooltipEvent.PostText event) {
        if (ICONS.isEmpty()) {
            return;
        }

        final List<? extends ITextProperties> lines = event.getLines();
        int index = -1;
        for (int i = 0; i < lines.size(); i++) {
            if (MARKER.equals(lines.get(i).getString())) {
                index = i;
                break;
            }
        }
        if (index < 0) {
            return;
        }

        final Minecraft mc = Minecraft.getInstance();
        final ItemRenderer itemRenderer = mc.getItemRenderer();
        final FontRenderer font = event.getFontRenderer() != null ? event.getFontRenderer() : mc.fontRenderer;

        final int x = event.getX();
        final int y = event.getY() + index * 10 + (index > 0 ? 2 : 0);

        final float oldZ = itemRenderer.zLevel;
        itemRenderer.zLevel = 400.0F;
        RenderSystem.enableDepthTest();

        int drawX = x;
        for (int i = 0; i < ICONS.size(); i++) {
            final ItemStack icon = ICONS.get(i);
            itemRenderer.renderItemAndEffectIntoGUI(icon, drawX, y);
            itemRenderer.renderItemOverlayIntoGUI(font, icon, drawX, y,
                    ReadableNumberConverter.INSTANCE.toSlimReadableForm(COUNTS.get(i)));
            drawX += 18;
        }
        if (hasMore) {
            font.drawStringWithShadow(event.getMatrixStack(), "...", drawX + 2, y + 5, 0xAAAAAA);
        }

        itemRenderer.zLevel = oldZ;
    }

}
''')

path = 'src/main/java/appeng/core/api/ApiClientHelper.java'
s = open(path).read()
if 'CellPreviewTooltip' not in s:
    old = ('    @Override\n'
           '    public <T extends IAEStack<T>> void addCellInformation(ICellInventoryHandler<T> handler,\n'
           '            List<ITextComponent> lines) {\n'
           '        if (handler == null) {\n')
    assert s.count(old) == 1, 'anchor not found in ApiClientHelper'
    s = s.replace(old,
        '    @Override\n'
        '    public <T extends IAEStack<T>> void addCellInformation(ICellInventoryHandler<T> handler,\n'
        '            List<ITextComponent> lines) {\n'
        '        addCellInformationBase(handler, lines);\n'
        '        appeng.client.render.CellPreviewTooltip.addPreview(handler, lines);\n'
        '    }\n'
        '\n'
        '    private <T extends IAEStack<T>> void addCellInformationBase(ICellInventoryHandler<T> handler,\n'
        '            List<ITextComponent> lines) {\n'
        '        if (handler == null) {\n')
    open(path, 'w').write(s)

path = 'src/main/java/appeng/client/ClientHelper.java'
s = open(path).read()
if 'CellPreviewTooltip' not in s:
    old = '        MinecraftForge.EVENT_BUS.addListener(this::wheelEvent);\n'
    assert s.count(old) == 1, 'anchor not found in ClientHelper'
    s = s.replace(old, old + '        MinecraftForge.EVENT_BUS.addListener(appeng.client.render.CellPreviewTooltip::onPostText);\n')
    open(path, 'w').write(s)
print('cell preview applied')
