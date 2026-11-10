# ===== Fluids in the item/crafting terminals (shown as dummy fluid items) =====
base = 'src/main/java/appeng/container/me/'

def edit(path, pairs):
    s = open(base + path).read()
    if 'getStorageListForClient' in s:
        return
    for old, new, count in pairs:
        assert s.count(old) == count, 'anchor not found %d time(s) in %s: %s' % (count, path, old)
        s = s.replace(old, new)
    open(base + path, 'w').write(s)

IMPORTS = '''package appeng.container.me.items;

import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.item.Items;
import net.minecraft.util.text.StringTextComponent;
import net.minecraftforge.fluids.FluidAttributes;
import net.minecraftforge.fluids.FluidStack;
import net.minecraftforge.fluids.FluidUtil;
import net.minecraftforge.fluids.capability.IFluidHandler;
import net.minecraftforge.fluids.capability.IFluidHandlerItem;

import appeng.api.config.Actionable;
import appeng.api.networking.security.IActionSource;
import appeng.api.networking.storage.IBaseMonitor;
import appeng.api.storage.IMEMonitor;
import appeng.api.storage.IMEMonitorHandlerReceiver;
import appeng.api.storage.channels.IFluidStorageChannel;
import appeng.api.storage.data.IAEFluidStack;
import appeng.api.storage.data.IItemList;
import appeng.fluids.items.FluidDummyItem;
import appeng.fluids.util.AEFluidStack;
'''

CODE = '''                Api.instance().storage().getStorageChannel(IItemStorageChannel.class));
        this.fluidMonitor = createFluidMonitor(host);
    }

    // ---- Fluids are shown in the grid as dummy fluid items ----

    private final FluidReceiver fluidReceiver = new FluidReceiver();
    private final IMEMonitor<IAEFluidStack> fluidMonitor;

    private IMEMonitor<IAEFluidStack> createFluidMonitor(ITerminalHost host) {
        if (!isServer()) {
            return null;
        }
        IMEMonitor<IAEFluidStack> result = host
                .getInventory(Api.instance().storage().getStorageChannel(IFluidStorageChannel.class));
        if (result != null) {
            result.addListener(this.fluidReceiver, null);
        }
        return result;
    }

    /**
     * Fluids are identified by a dummy item with an amount of 1, the real amount is the stack size.
     */
    private static IAEItemStack toDummy(IAEFluidStack fluid) {
        IAEFluidStack key = fluid.copy();
        key.setStackSize(1);
        ItemStack representation = key.asItemStackRepresentation();
        if (representation.isEmpty()) {
            return null;
        }
        return AEItemStack.fromItemStack(representation);
    }

    private class FluidReceiver implements IMEMonitorHandlerReceiver<IAEFluidStack> {
        @Override
        public boolean isValid(Object verificationToken) {
            return true;
        }

        @Override
        public void postChange(IBaseMonitor<IAEFluidStack> monitor, Iterable<IAEFluidStack> change,
                IActionSource source) {
            for (IAEFluidStack fluid : change) {
                IAEItemStack dummy = toDummy(fluid);
                if (dummy != null) {
                    addExtraChange(dummy);
                }
            }
        }

        @Override
        public void onListUpdate() {
            ItemTerminalContainer.this.onListUpdate();
        }
    }

    @Override
    protected IItemList<IAEItemStack> getStorageListForClient() {
        IItemList<IAEItemStack> items = super.getStorageListForClient();
        if (this.fluidMonitor == null) {
            return items;
        }
        IItemList<IAEFluidStack> fluids = this.fluidMonitor.getStorageList();
        if (fluids.isEmpty()) {
            return items;
        }
        IItemList<IAEItemStack> merged = this.getStorageChannel().createList();
        for (IAEItemStack item : items) {
            merged.add(item.copy());
        }
        for (IAEFluidStack fluid : fluids) {
            IAEItemStack dummy = toDummy(fluid);
            if (dummy != null) {
                dummy.setStackSize(fluid.getStackSize());
                merged.add(dummy);
            }
        }
        return merged;
    }

    @Override
    public void onContainerClosed(PlayerEntity player) {
        super.onContainerClosed(player);
        if (this.fluidMonitor != null) {
            this.fluidMonitor.removeListener(this.fluidReceiver);
        }
    }

    private static void say(ServerPlayerEntity player, String message) {
        player.sendStatusMessage(new StringTextComponent(message), true);
    }

    /**
     * Clicking a fluid hands the player a filled bucket. The empty bucket is taken from the system, so the system
     * must have one stored, otherwise nothing happens.
     */
    private void handleFluidInteraction(ServerPlayerEntity player, IAEItemStack dummy, InventoryAction action) {
        ItemStack held = player.inventory.getItemStack();
        if (!held.isEmpty()) {
            // Holding something: use the normal logic to put it into the network
            handleNetworkInteraction(player, null, action);
            return;
        }
        if (this.fluidMonitor == null || this.powerSource == null) {
            say(player, "This terminal cannot access fluids");
            return;
        }
        if (action != InventoryAction.PICKUP_OR_SET_DOWN && action != InventoryAction.SHIFT_CLICK) {
            return;
        }

        ItemStack dummyStack = dummy.getDefinition();
        FluidStack fluidStack = ((FluidDummyItem) dummyStack.getItem()).getFluidStack(dummyStack);
        if (fluidStack.isEmpty()) {
            return;
        }
        Item filledBucket = fluidStack.getFluid().getFilledBucket();
        if (filledBucket == Items.AIR) {
            say(player, "This fluid has no bucket");
            return;
        }

        // The system must have an empty bucket
        IAEItemStack emptyBucket = AEItemStack.fromItemStack(new ItemStack(Items.BUCKET));
        if (emptyBucket == null) {
            return;
        }
        emptyBucket.setStackSize(1);
        IAEItemStack bucketCheck = Platform.poweredExtraction(this.powerSource, this.monitor, emptyBucket.copy(),
                this.getActionSource(), Actionable.SIMULATE);
        if (bucketCheck == null || bucketCheck.getStackSize() < 1) {
            say(player, "The system has no empty bucket");
            return;
        }

        IAEFluidStack request = AEFluidStack
                .fromFluidStack(new FluidStack(fluidStack.getFluid(), FluidAttributes.BUCKET_VOLUME));
        if (request == null) {
            return;
        }
        IAEFluidStack possible = Platform.poweredExtraction(this.powerSource, this.fluidMonitor, request,
                this.getActionSource(), Actionable.SIMULATE);
        if (possible == null || possible.getStackSize() < FluidAttributes.BUCKET_VOLUME) {
            say(player, "The system has less than 1000 mB of this fluid");
            return;
        }
        IAEFluidStack extracted = Platform.poweredExtraction(this.powerSource, this.fluidMonitor, request,
                this.getActionSource());
        if (extracted == null) {
            say(player, "Could not extract the fluid");
            return;
        }
        if (extracted.getStackSize() < FluidAttributes.BUCKET_VOLUME) {
            this.fluidMonitor.injectItems(extracted, Actionable.MODULATE, this.getActionSource());
            return;
        }

        IAEItemStack bucket = Platform.poweredExtraction(this.powerSource, this.monitor, emptyBucket.copy(),
                this.getActionSource());
        if (bucket == null || bucket.getStackSize() < 1) {
            // Could not get the bucket after all: give the fluid back
            this.fluidMonitor.injectItems(extracted, Actionable.MODULATE, this.getActionSource());
            return;
        }

        ItemStack filled = new ItemStack(filledBucket);
        if (action == InventoryAction.PICKUP_OR_SET_DOWN) {
            player.inventory.setItemStack(filled);
            this.updateHeld(player);
        } else if (!player.inventory.addItemStackToInventory(filled)) {
            player.dropItem(filled, false);
        }
    }

    /**
     * Right-clicking with a filled bucket puts its fluid back into the system, if the system can store all of it.
     * Otherwise the bucket keeps its fluid. The emptied bucket goes into the system if it has room.
     *
     * @return true if the held item contains a fluid (so the click is handled here and nowhere else).
     */
    private boolean handleBucketReturn(ServerPlayerEntity player) {
        ItemStack held = player.inventory.getItemStack();
        if (held.isEmpty() || this.fluidMonitor == null || this.powerSource == null) {
            return false;
        }
        ItemStack single = held.copy();
        single.setCount(1);
        IFluidHandlerItem handler = FluidUtil.getFluidHandler(single).orElse(null);
        if (handler == null) {
            return false;
        }
        FluidStack contained = handler.drain(Integer.MAX_VALUE, IFluidHandler.FluidAction.SIMULATE);
        if (contained.isEmpty()) {
            return false;
        }

        IAEFluidStack toInsert = AEFluidStack.fromFluidStack(contained);
        if (toInsert == null) {
            return true;
        }
        IAEFluidStack leftover = Platform.poweredInsert(this.powerSource, this.fluidMonitor, toInsert.copy(),
                this.getActionSource(), Actionable.SIMULATE);
        if (leftover != null && leftover.getStackSize() > 0) {
            // No room for all of it: the bucket keeps its fluid
            say(player, "No room for this fluid in the system");
            return true;
        }
        leftover = Platform.poweredInsert(this.powerSource, this.fluidMonitor, toInsert.copy(),
                this.getActionSource());
        if (leftover != null && leftover.getStackSize() > 0) {
            // Only a part was stored: take it back out, the bucket keeps its fluid
            say(player, "No room for this fluid in the system");
            IAEFluidStack inserted = toInsert.copy();
            inserted.setStackSize(inserted.getStackSize() - leftover.getStackSize());
            if (inserted.getStackSize() > 0) {
                this.fluidMonitor.extractItems(inserted, Actionable.MODULATE, this.getActionSource());
            }
            return true;
        }

        // The fluid is in the system: empty the bucket
        handler.drain(contained, IFluidHandler.FluidAction.EXECUTE);
        ItemStack emptied = handler.getContainer();

        held.shrink(1);
        if (held.isEmpty()) {
            player.inventory.setItemStack(ItemStack.EMPTY);
        }

        // The empty bucket goes back into the system, or to the player if the system is full
        IAEItemStack emptiedAe = emptied.isEmpty() ? null : AEItemStack.fromItemStack(emptied);
        IAEItemStack notStored = emptiedAe == null ? null
                : Platform.poweredInsert(this.powerSource, this.monitor, emptiedAe, this.getActionSource());
        if (notStored != null && notStored.getStackSize() > 0) {
            ItemStack back = notStored.createItemStack();
            if (player.inventory.getItemStack().isEmpty()) {
                player.inventory.setItemStack(back);
            } else if (!player.inventory.addItemStackToInventory(back)) {
                player.dropItem(back, false);
            }
        }
        this.updateHeld(player);
        return true;
    }
'''

HEADER_OLD = '    protected void handleNetworkInteraction(ServerPlayerEntity player, @Nullable IAEItemStack stack,\n            InventoryAction action) {\n'
HEADER_NEW = HEADER_OLD + '''
        if (action == InventoryAction.SPLIT_OR_PLACE_SINGLE && handleBucketReturn(player)) {
            return;
        }

        if (stack != null && stack.getDefinition().getItem() instanceof FluidDummyItem) {
            handleFluidInteraction(player, stack, action);
            return;
        }
'''

edit('common/MEMonitorableContainer.java', [
    ('                    IItemList<T> storageList = monitor.getStorageList();\n',
     '                    IItemList<T> storageList = getStorageListForClient();\n', 1),
    ('    public boolean isPowered() {\n',
     '    /**\n'
     '     * The list of stacks that is sent to the client. Subclasses can add extra entries.\n'
     '     */\n'
     '    protected IItemList<T> getStorageListForClient() {\n'
     '        return this.monitor.getStorageList();\n'
     '    }\n'
     '\n'
     '    /**\n'
     '     * Lets subclasses report a change to an entry that does not come from the main monitor.\n'
     '     */\n'
     '    protected final void addExtraChange(T stack) {\n'
     '        this.updateHelper.addChange(stack);\n'
     '    }\n'
     '\n'
     '    public boolean isPowered() {\n', 1),
])

edit('items/ItemTerminalContainer.java', [
    ('package appeng.container.me.items;\n', IMPORTS, 1),
    ('                Api.instance().storage().getStorageChannel(IItemStorageChannel.class));\n    }\n', CODE, 1),
    (HEADER_OLD, HEADER_NEW, 1),
])
print('fluids applied')
