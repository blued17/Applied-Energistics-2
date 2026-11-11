# ===== Lock crafting for the ME Interface (like the Pattern Provider in newer AE2 versions) =====
api = 'src/api/java/appeng/api/config/'
main = 'src/main/java/appeng/'

def patch(path, pairs, marker):
    s = open(path).read()
    if marker in s:
        return
    for old, new, count in pairs:
        assert s.count(old) == count, 'anchor not found %d time(s) in %s: %s' % (count, path, old[:80])
        s = s.replace(old, new)
    open(path, 'w').write(s)

open(api + 'LockCraftingMode.java', 'w').write('''package appeng.api.config;

public enum LockCraftingMode {
    NONE,
    LOCK_WHILE_HIGH,
    LOCK_WHILE_LOW,
    LOCK_UNTIL_PULSE,
    LOCK_UNTIL_RESULT
}
''')

patch(api + 'Settings.java', [
    ('    BLOCK(EnumSet.of(YesNo.YES, YesNo.NO)),\n',
     '    BLOCK(EnumSet.of(YesNo.YES, YesNo.NO)),\n\n    LOCK_CRAFTING_MODE(EnumSet.allOf(LockCraftingMode.class)),\n', 1),
], 'LOCK_CRAFTING_MODE')

patch(main + 'core/localization/ButtonToolTips.java', [
    ('    Blocking, NonBlocking,\n',
     '    Blocking, NonBlocking,\n\n'
     '    LockCraftingMode, LockCraftingModeNone, LockCraftingWhileRedstoneHigh, LockCraftingWhileRedstoneLow,\n'
     '    LockCraftingUntilRedstonePulse, LockCraftingUntilResultReturned,\n', 1),
], 'LockCraftingUntilResultReturned')

lang = 'src/main/resources/assets/appliedenergistics2/lang/en_us.json'
s = open(lang).read().rstrip()
if 'LockCraftingMode' not in s:
    body = s[:-1].rstrip()
    s = body + ''',
  "gui.tooltips.appliedenergistics2.LockCraftingMode": "Lock Crafting",
  "gui.tooltips.appliedenergistics2.LockCraftingModeNone": "Never",
  "gui.tooltips.appliedenergistics2.LockCraftingWhileRedstoneHigh": "With redstone signal",
  "gui.tooltips.appliedenergistics2.LockCraftingWhileRedstoneLow": "Without redstone signal",
  "gui.tooltips.appliedenergistics2.LockCraftingUntilRedstonePulse": "Until redstone pulse is received",
  "gui.tooltips.appliedenergistics2.LockCraftingUntilResultReturned": "Until primary crafting result is returned"
}
'''
    open(lang, 'w').write(s)

patch(main + 'client/gui/widgets/SettingToggleButton.java', [
    ('            registerApp(Icon.BLOCKING_MODE_NO, Settings.BLOCK, YesNo.NO, ButtonToolTips.InterfaceBlockingMode,\n'
     '                    ButtonToolTips.NonBlocking);\n',
     '            registerApp(Icon.BLOCKING_MODE_NO, Settings.BLOCK, YesNo.NO, ButtonToolTips.InterfaceBlockingMode,\n'
     '                    ButtonToolTips.NonBlocking);\n'
     '\n'
     '            registerApp(Icon.REDSTONE_IGNORE, Settings.LOCK_CRAFTING_MODE,\n'
     '                    appeng.api.config.LockCraftingMode.NONE, ButtonToolTips.LockCraftingMode,\n'
     '                    ButtonToolTips.LockCraftingModeNone);\n'
     '            registerApp(Icon.REDSTONE_HIGH, Settings.LOCK_CRAFTING_MODE,\n'
     '                    appeng.api.config.LockCraftingMode.LOCK_WHILE_HIGH, ButtonToolTips.LockCraftingMode,\n'
     '                    ButtonToolTips.LockCraftingWhileRedstoneHigh);\n'
     '            registerApp(Icon.REDSTONE_LOW, Settings.LOCK_CRAFTING_MODE,\n'
     '                    appeng.api.config.LockCraftingMode.LOCK_WHILE_LOW, ButtonToolTips.LockCraftingMode,\n'
     '                    ButtonToolTips.LockCraftingWhileRedstoneLow);\n'
     '            registerApp(Icon.REDSTONE_PULSE, Settings.LOCK_CRAFTING_MODE,\n'
     '                    appeng.api.config.LockCraftingMode.LOCK_UNTIL_PULSE, ButtonToolTips.LockCraftingMode,\n'
     '                    ButtonToolTips.LockCraftingUntilRedstonePulse);\n'
     '            registerApp(Icon.ENTER, Settings.LOCK_CRAFTING_MODE,\n'
     '                    appeng.api.config.LockCraftingMode.LOCK_UNTIL_RESULT, ButtonToolTips.LockCraftingMode,\n'
     '                    ButtonToolTips.LockCraftingUntilResultReturned);\n', 1),
], 'LOCK_CRAFTING_MODE')

patch(main + 'container/implementations/InterfaceContainer.java', [
    ('    @GuiSync(3)\n    public YesNo bMode = YesNo.NO;\n',
     '    @GuiSync(3)\n    public YesNo bMode = YesNo.NO;\n\n'
     '    @GuiSync(7)\n    public appeng.api.config.LockCraftingMode lockCraftingMode = appeng.api.config.LockCraftingMode.NONE;\n', 1),
    ('        this.setBlockingMode((YesNo) cm.getSetting(Settings.BLOCK));\n',
     '        this.setBlockingMode((YesNo) cm.getSetting(Settings.BLOCK));\n'
     '        this.lockCraftingMode = (appeng.api.config.LockCraftingMode) cm.getSetting(Settings.LOCK_CRAFTING_MODE);\n', 1),
], 'lockCraftingMode')

patch(main + 'client/gui/implementations/InterfaceScreen.java', [
    ('    private final SettingToggleButton<YesNo> blockMode;\n',
     '    private final SettingToggleButton<YesNo> blockMode;\n'
     '    private final SettingToggleButton<appeng.api.config.LockCraftingMode> lockMode;\n', 1),
    ('        this.addToLeftToolbar(this.blockMode);\n',
     '        this.addToLeftToolbar(this.blockMode);\n\n'
     '        this.lockMode = new ServerSettingToggleButton<>(Settings.LOCK_CRAFTING_MODE,\n'
     '                appeng.api.config.LockCraftingMode.NONE);\n'
     '        this.addToLeftToolbar(this.lockMode);\n', 1),
    ('        this.blockMode.set(this.container.getBlockingMode());\n',
     '        this.blockMode.set(this.container.getBlockingMode());\n'
     '        this.lockMode.set(this.container.lockCraftingMode);\n', 1),
], 'lockMode')

DUAL = main + 'helpers/DualityInterface.java'
patch(DUAL, [
    ('        this.cm.registerSetting(Settings.BLOCK, YesNo.NO);\n',
     '        this.cm.registerSetting(Settings.BLOCK, YesNo.NO);\n'
     '        this.cm.registerSetting(Settings.LOCK_CRAFTING_MODE, appeng.api.config.LockCraftingMode.NONE);\n', 1),
    ('        this.cm.writeToNBT(data);\n        this.craftingTracker.writeToNBT(data);\n',
     '        this.cm.writeToNBT(data);\n        this.craftingTracker.writeToNBT(data);\n'
     '        if (this.unlockEvent != null) {\n'
     '            data.putByte("unlockEvent", (byte) (this.unlockEvent.ordinal() + 1));\n'
     '            if (this.unlockEvent == UnlockEvent.RESULT && this.unlockStack != null) {\n'
     '                final CompoundNBT unlockTag = new CompoundNBT();\n'
     '                this.unlockStack.writeToNBT(unlockTag);\n'
     '                data.put("unlockStack", unlockTag);\n'
     '            }\n'
     '        }\n', 1),
    ('        this.cm.readFromNBT(data);\n        this.readConfig();\n',
     '        this.cm.readFromNBT(data);\n'
     '        this.unlockEvent = null;\n'
     '        this.unlockStack = null;\n'
     '        final int savedUnlockEvent = data.getByte("unlockEvent");\n'
     '        if (savedUnlockEvent > 0 && savedUnlockEvent <= UnlockEvent.values().length) {\n'
     '            this.unlockEvent = UnlockEvent.values()[savedUnlockEvent - 1];\n'
     '            if (this.unlockEvent == UnlockEvent.RESULT) {\n'
     '                this.unlockStack = appeng.util.item.AEItemStack.fromNBT(data.getCompound("unlockStack"));\n'
     '                if (this.unlockStack == null) {\n'
     '                    this.unlockEvent = null;\n'
     '                }\n'
     '            }\n'
     '        }\n'
     '        this.readConfig();\n', 1),
    ('    public boolean pushPattern(final ICraftingPatternDetails patternDetails, final CraftingInventory table) {\n',
     '    public boolean pushPattern(final ICraftingPatternDetails patternDetails, final CraftingInventory table) {\n'
     '        if (this.isCraftingLocked()) {\n'
     '            return false;\n'
     '        }\n'
     '        final boolean pushed = this.pushPatternUnlocked(patternDetails, table);\n'
     '        if (pushed) {\n'
     '            this.onPatternPushed(patternDetails);\n'
     '        }\n'
     '        return pushed;\n'
     '    }\n'
     '\n'
     '    private boolean pushPatternUnlocked(final ICraftingPatternDetails patternDetails,\n'
     '            final CraftingInventory table) {\n', 1),
    ('    public boolean isBusy() {\n        if (this.hasItemsToSend()) {\n            return true;\n        }\n',
     '    public boolean isBusy() {\n        if (this.isCraftingLocked()) {\n            return true;\n        }\n'
     '        if (this.hasItemsToSend()) {\n            return true;\n        }\n', 1),
    ('                if (toStore != null) {\n                    diff -= toStore.getStackSize();\n                }\n',
     '                if (toStore != null) {\n                    diff -= toStore.getStackSize();\n                }\n'
     '                if (diff > 0) {\n                    this.onStackReturned(itemStack, diff);\n                }\n', 1),
    ('    @Override\n'
     '    public void updateSetting(final IConfigManager manager, final Settings settingName, final Enum<?> newValue) {\n'
     '        if (this.getInstalledUpgrades(Upgrades.CRAFTING) == 0) {\n'
     '            this.cancelCrafting();\n'
     '        }\n'
     '        this.iHost.saveChanges();\n'
     '    }\n',
     '''    // ---- Lock crafting ----

    private enum UnlockEvent {
        REDSTONE_POWER, REDSTONE_PULSE, RESULT
    }

    private UnlockEvent unlockEvent;
    private IAEItemStack unlockStack;

    private boolean isRedstonePowered() {
        final TileEntity tile = this.iHost.getTileEntity();
        if (tile == null || tile.getWorld() == null) {
            return false;
        }
        return tile.getWorld().isBlockPowered(tile.getPos());
    }

    private boolean isCraftingLocked() {
        final appeng.api.config.LockCraftingMode mode = (appeng.api.config.LockCraftingMode) this.cm
                .getSetting(Settings.LOCK_CRAFTING_MODE);

        if (mode == appeng.api.config.LockCraftingMode.LOCK_WHILE_LOW && !this.isRedstonePowered()) {
            return true;
        }
        if (mode == appeng.api.config.LockCraftingMode.LOCK_WHILE_HIGH && this.isRedstonePowered()) {
            return true;
        }

        // Redstone based unlocking is checked whenever the lock is asked about
        if (this.unlockEvent == UnlockEvent.REDSTONE_POWER && this.isRedstonePowered()) {
            this.unlockEvent = null;
            this.iHost.saveChanges();
        } else if (this.unlockEvent == UnlockEvent.REDSTONE_PULSE && !this.isRedstonePowered()) {
            this.unlockEvent = UnlockEvent.REDSTONE_POWER;
        }

        return this.unlockEvent != null;
    }

    private void onPatternPushed(final ICraftingPatternDetails patternDetails) {
        final appeng.api.config.LockCraftingMode mode = (appeng.api.config.LockCraftingMode) this.cm
                .getSetting(Settings.LOCK_CRAFTING_MODE);

        this.unlockEvent = null;
        this.unlockStack = null;

        if (mode == appeng.api.config.LockCraftingMode.LOCK_UNTIL_PULSE) {
            this.unlockEvent = this.isRedstonePowered() ? UnlockEvent.REDSTONE_PULSE : UnlockEvent.REDSTONE_POWER;
        } else if (mode == appeng.api.config.LockCraftingMode.LOCK_UNTIL_RESULT) {
            final java.util.List<IAEItemStack> outputs = patternDetails.getOutputs();
            if (outputs != null && !outputs.isEmpty() && outputs.get(0) != null) {
                this.unlockEvent = UnlockEvent.RESULT;
                this.unlockStack = outputs.get(0).copy();
            }
        }
        this.iHost.saveChanges();
    }

    /**
     * Called when items were sent from the interface into the network. This unlocks crafting that waits for the
     * primary result.
     */
    private void onStackReturned(final IAEItemStack what, final long amount) {
        if (this.unlockEvent != UnlockEvent.RESULT) {
            return;
        }
        if (this.unlockStack == null) {
            this.unlockEvent = null;
        } else if (this.unlockStack.equals(what)) {
            final long remaining = this.unlockStack.getStackSize() - amount;
            if (remaining <= 0) {
                this.unlockEvent = null;
                this.unlockStack = null;
            } else {
                this.unlockStack.setStackSize(remaining);
            }
        } else {
            return;
        }
        this.iHost.saveChanges();
    }

    @Override
    public void updateSetting(final IConfigManager manager, final Settings settingName, final Enum<?> newValue) {
        if (this.getInstalledUpgrades(Upgrades.CRAFTING) == 0) {
            this.cancelCrafting();
        }
        if (settingName == Settings.LOCK_CRAFTING_MODE) {
            this.unlockEvent = null;
            this.unlockStack = null;
        }
        this.iHost.saveChanges();
    }
''', 1),
], 'isCraftingLocked')
print('lock applied')
