package appeng.container.guisync;

import net.minecraft.network.PacketBuffer;

/**
 * Implemented by objects that can be synchronized with {@link GuiSync}. The class must also have a public constructor
 * that takes a single {@link PacketBuffer} argument and reads the object back.
 */
public interface PacketWritable {

    void writeToPacket(PacketBuffer data);

}
