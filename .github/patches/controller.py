# ===== Right-click the ME Controller to open the network status (like in newer AE2 versions) =====
base = 'src/main/java/appeng/'

path = base + 'tile/networking/ControllerTileEntity.java'
s = open(path).read()
if 'INetworkTool' not in s:
    old = 'public class ControllerTileEntity extends AENetworkPowerTileEntity {\n'
    assert s.count(old) == 1, 'anchor not found in ControllerTileEntity'
    s = s.replace(old,
        'public class ControllerTileEntity extends AENetworkPowerTileEntity\n'
        '        implements appeng.api.implementations.guiobjects.INetworkTool {\n'
        '\n'
        '    // The network status screen only needs the grid host of the "tool"\n'
        '    @Override\n'
        '    public appeng.api.networking.IGridHost getGridHost() {\n'
        '        return this;\n'
        '    }\n'
        '\n'
        '    @Override\n'
        '    public net.minecraftforge.items.IItemHandler getInventory() {\n'
        '        return null;\n'
        '    }\n'
        '\n'
        '    @Override\n'
        '    public net.minecraft.item.ItemStack getItemStack() {\n'
        '        return net.minecraft.item.ItemStack.EMPTY;\n'
        '    }\n')
    open(path, 'w').write(s)

path = base + 'block/networking/ControllerBlock.java'
s = open(path).read()
if 'NetworkStatusContainer' not in s:
    old = '    public ControllerBlock() {\n'
    assert s.count(old) == 1, 'anchor not found in ControllerBlock'
    s = s.replace(old,
        '''    @Override
    public net.minecraft.util.ActionResultType onActivated(final net.minecraft.world.World w,
            final net.minecraft.util.math.BlockPos pos, final net.minecraft.entity.player.PlayerEntity player,
            final net.minecraft.util.Hand hand, final @javax.annotation.Nullable net.minecraft.item.ItemStack heldItem,
            final net.minecraft.util.math.BlockRayTraceResult hit) {
        if (appeng.util.InteractionUtil.isInAlternateUseMode(player)) {
            return net.minecraft.util.ActionResultType.PASS;
        }

        final ControllerTileEntity tile = this.getTileEntity(w, pos);
        if (tile != null) {
            if (!w.isRemote()) {
                appeng.container.ContainerOpener.openContainer(
                        appeng.container.me.networktool.NetworkStatusContainer.TYPE, player,
                        appeng.container.ContainerLocator.forTileEntitySide(tile, hit.getFace()));
            }
            return net.minecraft.util.ActionResultType.func_233537_a_(w.isRemote());
        }

        return net.minecraft.util.ActionResultType.PASS;
    }

    public ControllerBlock() {
''')
    open(path, 'w').write(s)
print('controller applied')
