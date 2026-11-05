package appeng.client.gui.widgets;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

import javax.annotation.Nullable;

import com.mojang.blaze3d.matrix.MatrixStack;
import com.mojang.blaze3d.systems.RenderSystem;

import org.apache.commons.lang3.time.DurationFormatUtils;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.AbstractGui;
import net.minecraft.client.gui.FontRenderer;
import net.minecraft.client.renderer.Rectangle2d;
import net.minecraft.util.math.MathHelper;
import net.minecraft.util.text.ITextComponent;
import net.minecraft.util.text.StringTextComponent;
import net.minecraft.util.text.TextFormatting;
import net.minecraft.util.text.TranslationTextComponent;

import appeng.client.Point;
import appeng.client.gui.AEBaseScreen;
import appeng.client.gui.ICompositeWidget;
import appeng.client.gui.Tooltip;
import appeng.client.gui.style.Blitter;
import appeng.client.gui.style.PaletteColor;
import appeng.client.gui.style.ScreenStyle;
import appeng.container.me.crafting.CraftingStatusContainer;
import appeng.container.me.crafting.CraftingStatusContainer.CraftingCpuListEntry;
import appeng.util.ReadableNumberConverter;

public class CPUSelectionList implements ICompositeWidget {

    private static final int ROWS = 6;
    private static final float TEXT_SCALE = 0.666f;

    private static final String SELECTOR_TEXTURE = "guis/cpu_selector.png";
    private static final String ICON_TEXTURE = "guis/cpu_icons.png";

    private static final int PROGRESS_COLOR = 0xFF4A7FB0;
    private static final int PROGRESS_COLOR_SELECTED = 0xFF7DA9D2;

    private final AEBaseScreen<?> screen;
    private final CraftingStatusContainer container;
    private final Scrollbar scrollbar;
    private final int textColor;

    private Rectangle2d bounds = new Rectangle2d(0, 0, 0, 0);

    public CPUSelectionList(AEBaseScreen<?> screen, CraftingStatusContainer container, Scrollbar scrollbar,
            ScreenStyle style) {
        this.screen = screen;
        this.container = container;
        this.scrollbar = scrollbar;
        this.textColor = style.getColor(PaletteColor.DEFAULT_TEXT_COLOR).toARGB();
    }

    private static Blitter background() {
        return Blitter.texture(SELECTOR_TEXTURE, 256, 256).src(0, 0, 94, 164);
    }

    private static Blitter button(boolean selected) {
        return Blitter.texture(SELECTOR_TEXTURE, 256, 256).src(100, selected ? 22 : 0, 67, 22);
    }

    private static Blitter icon(int srcX, int srcY) {
        return Blitter.texture(ICON_TEXTURE, 256, 256).src(srcX, srcY, 10, 10);
    }

    private static final int BUTTON_WIDTH = 67;
    private static final int BUTTON_HEIGHT = 22;

    @Override
    public void setPosition(Point position) {
        this.bounds = new Rectangle2d(position.getX(), position.getY(), bounds.getWidth(), bounds.getHeight());
    }

    @Override
    public void setSize(int width, int height) {
        this.bounds = new Rectangle2d(bounds.getX(), bounds.getY(), width, height);
    }

    @Override
    public Rectangle2d getBounds() {
        return bounds;
    }

    private List<CraftingCpuListEntry> cpus() {
        return container.cpuList.getCpus();
    }

    @Override
    public boolean onMouseWheel(Point mousePos, double delta) {
        return scrollbar.onMouseWheel(mousePos, delta);
    }

    @Override
    public void updateBeforeRender() {
        int hiddenRows = Math.max(0, cpus().size() - ROWS);
        scrollbar.setRange(0, hiddenRows, Math.max(1, ROWS / 3));
    }

    @Override
    public boolean onMouseUp(Point mousePos, int button) {
        CraftingCpuListEntry cpu = hitTestCpu(mousePos.getX(), mousePos.getY());
        if (cpu != null) {
            container.selectCpu(cpu.getSerial());
            return true;
        }
        return false;
    }

    @Nullable
    private CraftingCpuListEntry hitTestCpu(int mouseX, int mouseY) {
        int relX = mouseX - bounds.getX() - 8;
        int relY = mouseY - bounds.getY() - 19;
        if (relX < 0 || relX >= BUTTON_WIDTH || relY < 0) {
            return null;
        }
        if (relY % (BUTTON_HEIGHT + 1) == BUTTON_HEIGHT) {
            return null;
        }
        int row = relY / (BUTTON_HEIGHT + 1);
        if (row >= ROWS) {
            return null;
        }
        int index = scrollbar.getCurrentScroll() + row;
        List<CraftingCpuListEntry> cpus = cpus();
        if (index >= 0 && index < cpus.size()) {
            return cpus.get(index);
        }
        return null;
    }

    @Nullable
    @Override
    public Tooltip getTooltip(int mouseX, int mouseY) {
        CraftingCpuListEntry cpu = hitTestCpu(mouseX, mouseY);
        if (cpu == null) {
            return null;
        }

        List<ITextComponent> lines = new ArrayList<>();
        lines.add(getCpuName(cpu));

        if (cpu.getCoProcessors() == 1) {
            lines.add(new TranslationTextComponent("gui.appliedenergistics2.CpuStatusCoProcessor",
                    cpu.getCoProcessors()).mergeStyle(TextFormatting.GRAY));
        } else if (cpu.getCoProcessors() > 1) {
            lines.add(new TranslationTextComponent("gui.appliedenergistics2.CpuStatusCoProcessors",
                    cpu.getCoProcessors()).mergeStyle(TextFormatting.GRAY));
        }

        lines.add(new TranslationTextComponent("gui.appliedenergistics2.CpuStatusStorage",
                formatBytes(cpu.getStorage())).mergeStyle(TextFormatting.GRAY));

        if (cpu.hasJob()) {
            lines.add(new TranslationTextComponent("gui.appliedenergistics2.CpuStatusCrafting",
                    new StringTextComponent(ReadableNumberConverter.INSTANCE.toWideReadableForm(cpu.getJobAmount()))
                            .appendString(" ").appendSibling(cpu.getJobItem().getDisplayName())));
            String percent = Math.round(cpu.getProgress() * 100) + "%";
            long millis = TimeUnit.NANOSECONDS.toMillis(cpu.getElapsedTimeNanos());
            lines.add(new TranslationTextComponent("gui.appliedenergistics2.CpuStatusCraftedIn", percent,
                    DurationFormatUtils.formatDuration(millis, "HH:mm:ss")));
        }
        return new Tooltip(lines);
    }

    @Override
    public void drawForegroundLayer(MatrixStack matrices, int zIndex, Rectangle2d dialogBounds, Point mouse) {
        FontRenderer font = Minecraft.getInstance().fontRenderer;

        background().dest(bounds.getX(), bounds.getY(), bounds.getWidth(), bounds.getHeight()).blit(matrices,
                zIndex);
        font.drawText(matrices, new TranslationTextComponent("gui.appliedenergistics2.CraftingCPUs"),
                bounds.getX() + 7, bounds.getY() + 7, textColor);

        List<CraftingCpuListEntry> cpus = cpus();
        int from = MathHelper.clamp(scrollbar.getCurrentScroll(), 0, cpus.size());
        int to = MathHelper.clamp(scrollbar.getCurrentScroll() + ROWS, 0, cpus.size());

        int x = bounds.getX() + 8;
        int y = bounds.getY() + 19;
        for (CraftingCpuListEntry cpu : cpus.subList(from, to)) {
            boolean selected = cpu.getSerial() == container.selectedCpuSerial;
            button(selected).dest(x, y).blit(matrices, zIndex);

            drawScaledText(matrices, font, getCpuName(cpu), x + 3, y + 2);

            if (cpu.hasJob()) {
                icon(208, 244).dest(x + 2, y + 9).blit(matrices, zIndex);
                drawScaledText(matrices, font,
                        new StringTextComponent(
                                ReadableNumberConverter.INSTANCE.toSlimReadableForm(cpu.getJobAmount())),
                        x + 14, y + 12);

                RenderSystem.pushMatrix();
                RenderSystem.translatef(x + 55, y + 9, 0);
                RenderSystem.scalef(TEXT_SCALE, TEXT_SCALE, 1);
                screen.drawItem(0, 0, cpu.getJobItem());
                RenderSystem.popMatrix();

                int progress = (int) (cpu.getProgress() * (BUTTON_WIDTH - 2));
                AbstractGui.fill(matrices, x + 1, y + BUTTON_HEIGHT - 3, x + 1 + progress, y + BUTTON_HEIGHT - 2,
                        selected ? PROGRESS_COLOR_SELECTED : PROGRESS_COLOR);
            } else {
                icon(208, 224).dest(x + 27, y + 9).blit(matrices, zIndex);
                drawScaledText(matrices, font, new StringTextComponent(formatBytes(cpu.getStorage())), x + 39,
                        y + 12);

                if (cpu.getCoProcessors() > 0) {
                    icon(208, 234).dest(x + 2, y + 9).blit(matrices, zIndex);
                    drawScaledText(matrices, font,
                            new StringTextComponent(
                                    ReadableNumberConverter.INSTANCE.toSlimReadableForm(cpu.getCoProcessors())),
                            x + 14, y + 12);
                }
            }

            y += BUTTON_HEIGHT + 1;
        }
    }

    private void drawScaledText(MatrixStack matrices, FontRenderer font, ITextComponent text, int x, int y) {
        matrices.push();
        matrices.translate(x, y, 0);
        matrices.scale(TEXT_SCALE, TEXT_SCALE, 1);
        font.drawText(matrices, text, 0, 0, textColor);
        matrices.pop();
    }

    private static ITextComponent getCpuName(CraftingCpuListEntry cpu) {
        if (cpu.getName() != null) {
            return cpu.getName();
        }
        return new TranslationTextComponent("gui.appliedenergistics2.CPUs").appendString(" #" + cpu.getSerial());
    }

    private static String formatBytes(long bytes) {
        String[] units = { "", "k", "m", "g", "t" };
        double value = bytes;
        int unit = 0;
        while (value >= 1024 && unit < units.length - 1) {
            value /= 1024;
            unit++;
        }
        if (value == Math.floor(value)) {
            return (long) value + units[unit];
        }
        return String.format("%.1f%s", value, units[unit]);
    }

        }
