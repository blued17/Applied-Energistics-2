# ===== Placement preview for cables and parts (like in newer AE2 versions) =====
base = 'src/main/java/appeng/client/'

open(base + 'render/PartPlacementPreview.java', 'w').write('''package appeng.client.render;

import java.util.ArrayList;
import java.util.List;

import com.mojang.blaze3d.matrix.MatrixStack;
import com.mojang.blaze3d.systems.RenderSystem;

import org.lwjgl.opengl.GL11;

import net.minecraft.block.BlockState;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.ActiveRenderInfo;
import net.minecraft.client.renderer.BufferBuilder;
import net.minecraft.client.renderer.Tessellator;
import net.minecraft.client.renderer.vertex.DefaultVertexFormats;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.tileentity.TileEntity;
import net.minecraft.util.Direction;
import net.minecraft.util.Hand;
import net.minecraft.util.math.AxisAlignedBB;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.BlockRayTraceResult;
import net.minecraft.util.math.RayTraceResult;
import net.minecraft.util.math.vector.Matrix4f;
import net.minecraft.util.math.vector.Vector3d;
import net.minecraft.world.World;
import net.minecraftforge.client.event.DrawHighlightEvent;

import appeng.api.implementations.parts.ICablePart;
import appeng.api.parts.IPart;
import appeng.api.parts.IPartHost;
import appeng.api.parts.IPartItem;
import appeng.api.util.AEPartLocation;
import appeng.parts.BusCollisionHelper;

/**
 * Shows where a cable or part will be placed while the player holds it, by drawing the outline of the part.
 */
public final class PartPlacementPreview {

    private PartPlacementPreview() {
    }

    private static final class Placement {
        final BlockPos pos;
        final Direction side;

        Placement(BlockPos pos, Direction side) {
            this.pos = pos;
            this.side = side;
        }
    }

    public static void onHighlight(DrawHighlightEvent.HighlightBlock event) {
        Minecraft mc = Minecraft.getInstance();
        PlayerEntity player = mc.player;
        World world = mc.world;
        if (player == null || world == null) {
            return;
        }

        ItemStack held = player.getHeldItem(Hand.MAIN_HAND);
        if (held.isEmpty() || !(held.getItem() instanceof IPartItem)) {
            return;
        }

        BlockRayTraceResult hit = event.getTarget();
        if (hit == null || hit.getType() != RayTraceResult.Type.BLOCK) {
            return;
        }

        Placement placement = getPlacement(world, held, hit.getPos(), hit.getFace());
        if (placement == null) {
            return;
        }

        ItemStack single = held.copy();
        single.setCount(1);
        IPart part = ((IPartItem<?>) held.getItem()).createPart(single);
        if (part == null) {
            return;
        }

        AEPartLocation location = part instanceof ICablePart ? AEPartLocation.INTERNAL
                : AEPartLocation.fromFacing(placement.side);
        List<AxisAlignedBB> boxes = new ArrayList<>();
        part.getBoxes(new BusCollisionHelper(boxes, location, true));
        if (boxes.isEmpty()) {
            return;
        }

        draw(event.getMatrix(), event.getInfo(), placement.pos, boxes);
    }

    private static IPartHost getHost(World world, BlockPos pos) {
        TileEntity tile = world.getTileEntity(pos);
        return tile instanceof IPartHost ? (IPartHost) tile : null;
    }

    private static boolean isFree(World world, BlockPos pos) {
        BlockState state = world.getBlockState(pos);
        return state.isAir(world, pos) || state.getMaterial().isReplaceable();
    }

    private static boolean canPlaceAt(World world, ItemStack held, BlockPos pos, Direction side) {
        IPartHost host = getHost(world, pos);
        if (host != null) {
            return host.canAddPart(held, AEPartLocation.fromFacing(side));
        }
        // A new cable bus block would be placed here
        return isFree(world, pos);
    }

    private static Placement getPlacement(World world, ItemStack held, BlockPos pos, Direction side) {
        IPartHost host = getHost(world, pos);
        if (host != null) {
            if (host.canAddPart(held, AEPartLocation.fromFacing(side))) {
                return new Placement(pos, side);
            }
            // Otherwise it goes into the neighbouring block
            BlockPos neighbour = pos.offset(side);
            if (canPlaceAt(world, held, neighbour, side.getOpposite())) {
                return new Placement(neighbour, side.getOpposite());
            }
            return null;
        }

        if (isFree(world, pos)) {
            return new Placement(pos, side);
        }

        BlockPos neighbour = pos.offset(side);
        if (canPlaceAt(world, held, neighbour, side.getOpposite())) {
            return new Placement(neighbour, side.getOpposite());
        }
        return null;
    }

    private static void draw(MatrixStack matrices, ActiveRenderInfo info, BlockPos pos, List<AxisAlignedBB> boxes) {
        Vector3d camera = info.getProjectedView();
        double ox = pos.getX() - camera.x;
        double oy = pos.getY() - camera.y;
        double oz = pos.getZ() - camera.z;
        Matrix4f matrix = matrices.getLast().getMatrix();

        RenderSystem.disableTexture();
        RenderSystem.enableBlend();
        RenderSystem.defaultBlendFunc();
        RenderSystem.enableDepthTest();
        RenderSystem.depthMask(false);
        RenderSystem.lineWidth(2.5F);

        // Faint outline that is also visible through blocks
        RenderSystem.depthFunc(GL11.GL_GREATER);
        drawBoxes(matrix, boxes, ox, oy, oz, 0.25F);

        // Normal outline
        RenderSystem.depthFunc(GL11.GL_LEQUAL);
        drawBoxes(matrix, boxes, ox, oy, oz, 0.7F);

        RenderSystem.lineWidth(1.0F);
        RenderSystem.depthMask(true);
        RenderSystem.disableBlend();
        RenderSystem.enableTexture();
    }

    private static void drawBoxes(Matrix4f matrix, List<AxisAlignedBB> boxes, double ox, double oy, double oz,
            float alpha) {
        BufferBuilder buffer = Tessellator.getInstance().getBuffer();
        buffer.begin(GL11.GL_LINES, DefaultVertexFormats.POSITION_COLOR);
        for (AxisAlignedBB box : boxes) {
            float x1 = (float) (ox + box.minX);
            float y1 = (float) (oy + box.minY);
            float z1 = (float) (oz + box.minZ);
            float x2 = (float) (ox + box.maxX);
            float y2 = (float) (oy + box.maxY);
            float z2 = (float) (oz + box.maxZ);

            // bottom
            line(buffer, matrix, x1, y1, z1, x2, y1, z1, alpha);
            line(buffer, matrix, x2, y1, z1, x2, y1, z2, alpha);
            line(buffer, matrix, x2, y1, z2, x1, y1, z2, alpha);
            line(buffer, matrix, x1, y1, z2, x1, y1, z1, alpha);
            // top
            line(buffer, matrix, x1, y2, z1, x2, y2, z1, alpha);
            line(buffer, matrix, x2, y2, z1, x2, y2, z2, alpha);
            line(buffer, matrix, x2, y2, z2, x1, y2, z2, alpha);
            line(buffer, matrix, x1, y2, z2, x1, y2, z1, alpha);
            // sides
            line(buffer, matrix, x1, y1, z1, x1, y2, z1, alpha);
            line(buffer, matrix, x2, y1, z1, x2, y2, z1, alpha);
            line(buffer, matrix, x2, y1, z2, x2, y2, z2, alpha);
            line(buffer, matrix, x1, y1, z2, x1, y2, z2, alpha);
        }
        Tessellator.getInstance().draw();
    }

    private static void line(BufferBuilder buffer, Matrix4f matrix, float x1, float y1, float z1, float x2,
            float y2, float z2, float alpha) {
        buffer.pos(matrix, x1, y1, z1).color(1.0F, 1.0F, 1.0F, alpha).endVertex();
        buffer.pos(matrix, x2, y2, z2).color(1.0F, 1.0F, 1.0F, alpha).endVertex();
    }

}
''')

path = base + 'ClientHelper.java'
s = open(path).read()
if 'PartPlacementPreview' not in s:
    old = '        MinecraftForge.EVENT_BUS.addListener(this::wheelEvent);\n'
    assert s.count(old) == 1, 'anchor not found in ClientHelper'
    s = s.replace(old, old + '        MinecraftForge.EVENT_BUS.addListener(appeng.client.render.PartPlacementPreview::onHighlight);\n')
    open(path, 'w').write(s)
print('preview applied')
