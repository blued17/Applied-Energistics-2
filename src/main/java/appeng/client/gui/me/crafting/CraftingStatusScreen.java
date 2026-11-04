
package appeng.client.gui.me.crafting;

import net.minecraft.entity.player.PlayerInventory;
import net.minecraft.util.text.ITextComponent;

import appeng.client.gui.implementations.AESubScreen;
import appeng.client.gui.style.ScreenStyle;
import appeng.client.gui.widgets.CPUSelectionList;
import appeng.client.gui.widgets.Scrollbar;
import appeng.container.me.crafting.CraftingStatusContainer;

public class CraftingStatusScreen extends CraftingCPUScreen<CraftingStatusContainer> {

    public CraftingStatusScreen(CraftingStatusContainer container, PlayerInventory playerInventory,
            ITextComponent title, ScreenStyle style) {
        super(container, playerInventory, title, style);

        AESubScreen subGui = new AESubScreen(container.getTarget());
        subGui.addBackButton("back", widgets);

        Scrollbar scrollbar = new Scrollbar() {
            @Override
            public boolean wantsAllMouseWheelEvents() {
                return false;
            }
        };
        widgets.add("selectCpuScrollbar", scrollbar);
        widgets.add("selectCpuList", new CPUSelectionList(this, container, scrollbar, style));
    }

    @Override
    protected ITextComponent getGuiDisplayName(final ITextComponent in) {
        return in;
    }

}
