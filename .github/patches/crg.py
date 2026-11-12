# ===== Crystal Resonance Generator (generates AE without fuel, one per network) =====
import json

java = 'src/main/java/appeng/'
res = 'src/main/resources/'
NAME = 'crystal_resonance_generator'

open(java + 'block/networking/CrystalResonanceGeneratorBlock.java', 'w').write('''package appeng.block.networking;

import net.minecraft.block.SoundType;
import net.minecraft.block.material.Material;

import appeng.block.AEBaseTileBlock;
import appeng.tile.networking.CrystalResonanceGeneratorTileEntity;

public class CrystalResonanceGeneratorBlock extends AEBaseTileBlock<CrystalResonanceGeneratorTileEntity> {

    public CrystalResonanceGeneratorBlock() {
        super(defaultProps(Material.ROCK).sound(SoundType.METAL).notSolid());
    }

}
''')

open(java + 'tile/networking/CrystalResonanceGeneratorTileEntity.java', 'w').write('''package appeng.tile.networking;

import java.util.EnumSet;

import net.minecraft.tileentity.TileEntityType;
import net.minecraft.util.Direction;

import appeng.api.config.Actionable;
import appeng.api.networking.IGrid;
import appeng.api.networking.IGridNode;
import appeng.api.networking.ticking.IGridTickable;
import appeng.api.networking.ticking.TickRateModulation;
import appeng.api.networking.ticking.TickingRequest;
import appeng.api.util.AECableType;
import appeng.api.util.AEPartLocation;
import appeng.me.GridAccessException;
import appeng.tile.grid.AENetworkTileEntity;

/**
 * Generates energy for the network without fuel. Only one generator per network works.
 */
public class CrystalResonanceGeneratorTileEntity extends AENetworkTileEntity implements IGridTickable {

    /**
     * AE generated per tick.
     */
    private static final double GENERATION_PER_TICK = 20;

    private static final int TICK_RATE = 10;

    public CrystalResonanceGeneratorTileEntity(TileEntityType<?> tileEntityTypeIn) {
        super(tileEntityTypeIn);
        this.getProxy().setIdlePowerUsage(0);
        this.getProxy().setFlags();
        this.getProxy().setValidSides(EnumSet.of(Direction.DOWN));
    }

    @Override
    public AECableType getCableConnectionType(final AEPartLocation dir) {
        return AECableType.SMART;
    }

    @Override
    public TickingRequest getTickingRequest(final IGridNode node) {
        return new TickingRequest(TICK_RATE, TICK_RATE, false, false);
    }

    @Override
    public TickRateModulation tickingRequest(final IGridNode node, final int ticksSinceLastCall) {
        try {
            final IGrid grid = this.getProxy().getGrid();

            // Only the generator with the lowest position generates energy
            final long myPos = this.getPos().toLong();
            for (final IGridNode other : grid.getMachines(CrystalResonanceGeneratorTileEntity.class)) {
                if (other.getMachine() instanceof CrystalResonanceGeneratorTileEntity) {
                    final CrystalResonanceGeneratorTileEntity tile = (CrystalResonanceGeneratorTileEntity) other
                            .getMachine();
                    if (tile != this && tile.getPos().toLong() < myPos) {
                        return TickRateModulation.SAME;
                    }
                }
            }

            this.getProxy().getEnergy().injectPower(GENERATION_PER_TICK * ticksSinceLastCall, Actionable.MODULATE);
        } catch (final GridAccessException e) {
            // not connected
        }
        return TickRateModulation.SAME;
    }

}
''')

# ---- registration in ApiBlocks ----
path = java + 'core/api/definitions/ApiBlocks.java'
s = open(path).read()
if 'crystalResonanceGenerator' not in s:
    field = '    private final ITileDefinition quartzGrowthAccelerator;\n'
    assert s.count(field) == 1, 'field anchor'
    s = s.replace(field, field + '    private final ITileDefinition crystalResonanceGenerator;\n')
    stmt = ('        this.quartzGrowthAccelerator = registry.block("quartz_growth_accelerator", QuartzGrowthAcceleratorBlock::new)\n'
            '                .tileEntity(registry.tileEntity("quartz_growth_accelerator", QuartzGrowthAcceleratorTileEntity.class,\n'
            '                        QuartzGrowthAcceleratorTileEntity::new).build())\n'
            '                .features(AEFeature.CRYSTAL_GROWTH_ACCELERATOR).build();\n')
    assert s.count(stmt) == 1, 'statement anchor'
    s = s.replace(stmt, stmt +
        '        this.crystalResonanceGenerator = registry\n'
        '                .block("crystal_resonance_generator", appeng.block.networking.CrystalResonanceGeneratorBlock::new)\n'
        '                .tileEntity(registry.tileEntity("crystal_resonance_generator",\n'
        '                        appeng.tile.networking.CrystalResonanceGeneratorTileEntity.class,\n'
        '                        appeng.tile.networking.CrystalResonanceGeneratorTileEntity::new).build())\n'
        '                .features(AEFeature.POWER_GEN).rendering(new BlockRenderingCustomizer() {\n'
        '                    @Override\n'
        '                    @OnlyIn(Dist.CLIENT)\n'
        '                    public void customize(IBlockRendering rendering, IItemRendering itemRendering) {\n'
        '                        rendering.renderType(RenderType.getCutout());\n'
        '                    }\n'
        '                }).build();\n')
    open(path, 'w').write(s)

# ---- resources ----
model = open('/tmp/crg_model.json').read().replace('ae2:', 'appliedenergistics2:')
json.loads(model)
open(res + 'assets/appliedenergistics2/models/block/' + NAME + '.json', 'w').write(model)
open(res + 'assets/appliedenergistics2/models/item/' + NAME + '.json', 'w').write(
    '{\n  "parent": "appliedenergistics2:block/' + NAME + '"\n}\n')
open(res + 'assets/appliedenergistics2/blockstates/' + NAME + '.json', 'w').write(
    '{\n  "variants": {\n    "": {\n      "model": "appliedenergistics2:block/' + NAME + '"\n    }\n  }\n}\n')
import shutil
shutil.copyfile('/tmp/crg.png', res + 'assets/appliedenergistics2/textures/block/crg.png')

import os
recipe_dir = res + 'data/appliedenergistics2/recipes/network/blocks/'
os.makedirs(recipe_dir, exist_ok=True)
open(recipe_dir + NAME + '.json', 'w').write('''{
  "type": "minecraft:crafting_shaped",
  "conditions": [
    {
      "type": "forge:not",
      "value": {
        "type": "forge:tag_empty",
        "tag": "forge:ingots/copper"
      }
    }
  ],
  "pattern": [
    "cfc",
    "cqc",
    "iii"
  ],
  "key": {
    "c": {
      "tag": "forge:ingots/copper"
    },
    "f": {
      "item": "appliedenergistics2:fluix_block"
    },
    "q": {
      "item": "appliedenergistics2:charged_certus_quartz_crystal"
    },
    "i": {
      "tag": "forge:ingots/iron"
    }
  },
  "result": {
    "item": "appliedenergistics2:crystal_resonance_generator"
  }
}
''')

lang = res + 'assets/appliedenergistics2/lang/en_us.json'
s = open(lang).read().rstrip()
if NAME not in s:
    s = s[:-1].rstrip() + ',\n  "block.appliedenergistics2.crystal_resonance_generator": "Crystal Resonance Generator"\n}\n'
    open(lang, 'w').write(s)
    json.loads(s)
print('crystal resonance generator applied')
