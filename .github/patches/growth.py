# ===== Growth accelerator also accelerates crops, saplings and similar plants =====
path = 'src/main/java/appeng/tile/misc/QuartzGrowthAcceleratorTileEntity.java'
s = open(path).read()
if 'isGrowable' not in s:
    def rep(old, new):
        global s
        assert s.count(old) == 1, 'anchor not found exactly once: ' + old[:80]
        s = s.replace(old, new)

    rep('        implements IPowerChannelState, ICrystalGrowthAccelerator {\n',
        '        implements IPowerChannelState, ICrystalGrowthAccelerator,\n'
        '        appeng.api.networking.ticking.IGridTickable {\n')

    rep('    @Override\n    public AECableType getCableConnectionType(final AEPartLocation dir) {\n        return AECableType.COVERED;\n    }\n',
        '''    private static final int GROWTH_TICK_RATE = 10;

    @Override
    public appeng.api.networking.ticking.TickingRequest getTickingRequest(final appeng.api.networking.IGridNode node) {
        return new appeng.api.networking.ticking.TickingRequest(GROWTH_TICK_RATE, GROWTH_TICK_RATE, false, false);
    }

    @Override
    public appeng.api.networking.ticking.TickRateModulation tickingRequest(final appeng.api.networking.IGridNode node,
            final int ticksSinceLastCall) {
        if (this.getWorld() instanceof net.minecraft.world.server.ServerWorld && this.isPowered()) {
            final net.minecraft.world.server.ServerWorld serverWorld = (net.minecraft.world.server.ServerWorld) this
                    .getWorld();
            for (final Direction dir : Direction.values()) {
                final net.minecraft.util.math.BlockPos adjacent = this.getPos().offset(dir);
                final net.minecraft.block.BlockState state = serverWorld.getBlockState(adjacent);
                if (isGrowable(state)) {
                    state.randomTick(serverWorld, adjacent, serverWorld.rand);
                }
            }
        }
        return appeng.api.networking.ticking.TickRateModulation.SAME;
    }

    private static boolean isGrowable(final net.minecraft.block.BlockState state) {
        final net.minecraft.block.Block block = state.getBlock();
        return state.isIn(net.minecraft.tags.BlockTags.CROPS) || state.isIn(net.minecraft.tags.BlockTags.SAPLINGS)
                || block instanceof net.minecraft.block.CropsBlock || block instanceof net.minecraft.block.StemBlock
                || block instanceof net.minecraft.block.NetherWartBlock
                || block instanceof net.minecraft.block.SweetBerryBushBlock
                || block instanceof net.minecraft.block.CocoaBlock || block instanceof net.minecraft.block.SugarCaneBlock
                || block instanceof net.minecraft.block.CactusBlock || block instanceof net.minecraft.block.BambooBlock;
    }

    @Override
    public AECableType getCableConnectionType(final AEPartLocation dir) {
        return AECableType.COVERED;
    }
''')
    open(path, 'w').write(s)
print('growth applied')
