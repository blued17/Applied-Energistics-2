# ===== Cell and energy tooltips like in newer AE2 versions =====
base = 'src/main/java/appeng/core/'

open(base + 'localization/CellTooltips.java', 'w').write('''package appeng.core.localization;

import java.text.MessageFormat;
import java.util.Locale;

import net.minecraft.util.text.Color;
import net.minecraft.util.text.IFormattableTextComponent;
import net.minecraft.util.text.ITextComponent;
import net.minecraft.util.text.StringTextComponent;
import net.minecraft.util.text.Style;
import net.minecraft.util.text.TextFormatting;

import appeng.api.config.PowerUnits;

/**
 * Builds the tooltip lines for stored energy, used bytes and used types.
 */
public final class CellTooltips {

    private static final String[] UNITS = { "k", "M", "G", "T", "P", "E" };
    private static final long[] DIVISORS = { 1000L, 1000000L, 1000000000L, 1000000000000L, 1000000000000000L,
            1000000000000000000L };
    private static final int NUMBER_COLOR = 0x886EFF;
    private static final int UNIT_COLOR = 0xFFDE7D;

    private CellTooltips() {
    }

    private static IFormattableTextComponent colored(String text, int rgb) {
        return new StringTextComponent(text).setStyle(Style.EMPTY.setColor(Color.fromInt(rgb)));
    }

    private static IFormattableTextComponent gray() {
        return new StringTextComponent("").mergeStyle(TextFormatting.GRAY);
    }

    /**
     * Goes from red to green. If oneIsGreen is false, 0 is green and 1 is red.
     */
    private static int ratioColor(double ratio, boolean oneIsGreen) {
        double p = ratio;
        if (!oneIsGreen) {
            p = 1 - p;
        }
        int r = (int) (255d * (Math.max(0, Math.min(2 - 2 * p, 1))));
        int g = (int) (255d * (Math.max(0, Math.min(2 * p, 1))));
        return (r << 16) + (g << 8);
    }

    private static String amount(double amount, double divisor) {
        double fract = amount / divisor;
        String result;
        if (fract < 10) {
            result = String.format(Locale.ROOT, "%.3f", fract);
        } else if (fract < 100) {
            result = String.format(Locale.ROOT, "%.2f", fract);
        } else {
            result = String.format(Locale.ROOT, "%.1f", fract);
        }
        if (result.indexOf('.') >= 0) {
            while (result.endsWith("0")) {
                result = result.substring(0, result.length() - 1);
            }
            if (result.endsWith(".")) {
                result = result.substring(0, result.length() - 1);
            }
        }
        return result;
    }

    /**
     * @return the amount, the maximum and the unit, all using the same unit.
     */
    private static String[] maxed(double amount, double max) {
        if (max < 10000) {
            return new String[] { amount(amount, 1), amount(max, 1), "" };
        }
        int i = 0;
        while (i < DIVISORS.length - 1 && max / DIVISORS[i] >= 1000) {
            i++;
        }
        return new String[] { amount(amount, DIVISORS[i]), amount(max, DIVISORS[i]), UNITS[i] };
    }

    /**
     * Stored Energy: 0/20k AE (0%)
     */
    public static ITextComponent energy(double energy, double max) {
        String[] values = maxed(energy, max);
        double percent = max > 0 ? energy / max : 0;

        IFormattableTextComponent line = gray();
        line.appendSibling(GuiText.StoredEnergy.text());
        line.appendString(": ");
        line.appendSibling(colored(values[0] + "/" + values[1], NUMBER_COLOR));
        if (!values[2].isEmpty()) {
            line.appendSibling(colored(values[2], UNIT_COLOR));
        }
        line.appendString(" ");
        line.appendSibling(PowerUnits.AE.textComponent());
        line.appendString(" (");
        line.appendSibling(colored(MessageFormat.format("{0,number,#.##%}", percent), ratioColor(percent, true)));
        line.appendString(")");
        return line;
    }

    /**
     * 0 of 512 Bytes Used
     */
    public static ITextComponent bytesUsed(long bytes, long max) {
        double ratio = max > 0 ? (double) bytes / max : 0;

        IFormattableTextComponent numbers = new StringTextComponent("");
        numbers.appendSibling(colored(String.valueOf(bytes), ratioColor(ratio, false)));
        numbers.appendString(" ");
        numbers.appendSibling(GuiText.Of.text());
        numbers.appendString(" ");
        numbers.appendSibling(colored(String.valueOf(max), NUMBER_COLOR));

        return GuiText.BytesUsed.text(numbers).mergeStyle(TextFormatting.GRAY);
    }

    /**
     * 0 of 54 Types
     */
    public static ITextComponent typesUsed(long types, long max) {
        double ratio = max > 0 ? (double) types / max : 0;

        IFormattableTextComponent line = gray();
        line.appendSibling(colored(String.valueOf(types), ratioColor(ratio, false)));
        line.appendString(" ");
        line.appendSibling(GuiText.Of.text());
        line.appendString(" ");
        line.appendSibling(colored(String.valueOf(max), NUMBER_COLOR));
        line.appendString(" ");
        line.appendSibling(GuiText.Types.text());
        return line;
    }

}
''')

def edit(path, pairs):
    s = open(base + path).read()
    if 'CellTooltips' in s:
        return
    for old, new, count in pairs:
        assert s.count(old) == count, 'anchor not found %d time(s) in %s: %s' % (count, path, old[:80])
        s = s.replace(old, new)
    open(base + path, 'w').write(s)

edit('api/ApiClientHelper.java', [
    ('            lines.add(new StringTextComponent(cellInventory.getUsedBytes() + " ").appendSibling(GuiText.Of.text())\n'
     '                    .appendString(" " + cellInventory.getTotalBytes() + " ").appendSibling(GuiText.BytesUsed.text()));\n'
     '\n'
     '            lines.add(new StringTextComponent(cellInventory.getStoredItemTypes() + " ").appendSibling(GuiText.Of.text())\n'
     '                    .appendString(" " + cellInventory.getTotalItemTypes() + " ").appendSibling(GuiText.Types.text()));\n',
     '            lines.add(appeng.core.localization.CellTooltips.bytesUsed(cellInventory.getUsedBytes(),\n'
     '                    cellInventory.getTotalBytes()));\n'
     '            lines.add(appeng.core.localization.CellTooltips.typesUsed(cellInventory.getStoredItemTypes(),\n'
     '                    cellInventory.getTotalItemTypes()));\n', 1),
])

path = 'src/main/java/appeng/items/tools/powered/powersink/AEBasePoweredItem.java'
s = open(path).read()
if 'CellTooltips' not in s:
    old = ('        final double percent = internalCurrentPower / internalMaxPower;\n'
           '\n'
           '        lines.add(GuiText.StoredEnergy.text().deepCopy()\n'
           '                .appendString(\':\' + MessageFormat.format(" {0,number,#} ", internalCurrentPower))\n'
           '                .appendSibling(PowerUnits.AE.textComponent())\n'
           '                .appendString(" - " + MessageFormat.format(" {0,number,#.##%} ", percent)));\n')
    assert s.count(old) == 1, 'anchor not found in AEBasePoweredItem'
    s = s.replace(old, '        lines.add(appeng.core.localization.CellTooltips.energy(internalCurrentPower, internalMaxPower));\n')
    open(path, 'w').write(s)
print('tooltips applied')
