package appeng.container.guisync;

import net.minecraft.network.PacketBuffer;

public interface PacketWritable {

    void writeToPacket(PacketBuffer data);

}
