package appeng.container.me.crafting;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;
import java.util.WeakHashMap;

import com.google.common.collect.ImmutableSet;

import net.minecraft.entity.player.PlayerInventory;
import net.minecraft.inventory.container.ContainerType;
import net.minecraft.item.ItemStack;
import net.minecraft.network.PacketBuffer;
import net.minecraft.util.text.ITextComponent;

import appeng.api.config.SecurityPermissions;
import appeng.api.networking.IGrid;
import appeng.api.networking.crafting.ICraftingCPU;
import appeng.api.networking.crafting.ICraftingGrid;
import appeng.api.storage.ITerminalHost;
import appeng.api.storage.data.IAEItemStack;
import appeng.container.guisync.GuiSync;
import appeng.container.guisync.PacketWritable;
import appeng.container.implementations.ContainerTypeBuilder;
import appeng.me.cluster.implementations.CraftingCPUCluster;

public class CraftingStatusContainer extends CraftingCPUContainer implements CraftingCPUCyclingContainer {

    public static final ContainerType<CraftingStatusContainer> TYPE = ContainerTypeBuilder
            .create(CraftingStatusContainer::new, ITerminalHost.class)
            .requirePermission(SecurityPermissions.CRAFT)
            .build("craftingstatus");

    private static final CraftingCpuList EMPTY_CPU_LIST = new CraftingCpuList(Collections.emptyList());

    private static final Comparator<CraftingCpuListEntry> CPU_COMPARATOR = Comparator
            .comparing((CraftingCpuListEntry e) -> e.getName() == null)
            .thenComparing(e -> e.getName() != null ? e.getName().getString() : "")
            .thenComparingInt(CraftingCpuListEntry::getSerial);

    private static final String ACTION_SELECT_CPU = "selectCpu";

    private final WeakHashMap<ICraftingCPU, Integer> cpuSerialMap = new WeakHashMap<>();
    private int nextCpuSerial = 1;
    private ImmutableSet<ICraftingCPU> lastCpuSet = ImmutableSet.of();
    private int lastUpdate = 0;
    private ICraftingCPU selectedCpu = null;

    @GuiSync(6)
    public CraftingCpuList cpuList = EMPTY_CPU_LIST;

    @GuiSync(7)
    public int selectedCpuSerial = -1;

    public CraftingStatusContainer(int id, final PlayerInventory ip, final ITerminalHost te) {
        super(TYPE, id, ip, te);
        registerClientAction(ACTION_SELECT_CPU, Integer.class, this::selectCpu);
    }

    @Override
    protected void setCPU(ICraftingCPU c) {
        super.setCPU(c);
        this.selectedCpu = c;
        this.selectedCpuSerial = c != null ? getOrAssignCpuSerial(c) : -1;
    }

    @Override
    public void detectAndSendChanges() {
        IGrid network = this.getGrid();
        if (isServer()) {
            if (network != null) {
                ICraftingGrid craftingGrid = network.getCache(ICraftingGrid.class);
                ImmutableSet<ICraftingCPU> cpus = craftingGrid.getCpus();
                if (!lastCpuSet.equals(cpus) || ++lastUpdate >= 20) {
                    lastUpdate = 0;
                    lastCpuSet = cpus;
                    cpuList = createCpuList();
                }
            } else if (!lastCpuSet.isEmpty()) {
                lastCpuSet = ImmutableSet.of();
                cpuList = EMPTY_CPU_LIST;
            }

            if (selectedCpuSerial != -1) {
                boolean found = false;
                for (CraftingCpuListEntry entry : cpuList.getCpus()) {
                    if (entry.getSerial() == selectedCpuSerial) {
                        found = true;
                        break;
                    }
                }
                if (!found) {
                    selectCpu(-1);
                }
            }

            if (selectedCpuSerial == -1) {
                for (CraftingCpuListEntry entry : cpuList.getCpus()) {
                    if (entry.hasJob()) {
                        selectCpu(entry.getSerial());
                        break;
                    }
                }
                if (selectedCpuSerial == -1 && !cpuList.getCpus().isEmpty()) {
                    selectCpu(cpuList.getCpus().get(0).getSerial());
                }
            }
        }

        super.detectAndSendChanges();
    }

    private CraftingCpuList createCpuList() {
        List<CraftingCpuListEntry> entries = new ArrayList<>(lastCpuSet.size());
        for (ICraftingCPU cpu : lastCpuSet) {
            int serial = getOrAssignCpuSerial(cpu);

            ItemStack job = ItemStack.EMPTY;
            long jobAmount = 0;
            float progress = 0;
            long elapsed = 0;
            if (cpu instanceof CraftingCPUCluster && cpu.isBusy()) {
                CraftingCPUCluster cluster = (CraftingCPUCluster) cpu;
                IAEItemStack output = cluster.getFinalOutput();
                if (output != null) {
                    job = output.asItemStackRepresentation();
                    job.setCount(1);
                    jobAmount = output.getStackSize();
                }
                long start = cluster.getStartItemCount();
                if (start > 0) {
                    double done = (start - cluster.getRemainingItemCount()) / (double) start;
                    progress = (float) Math.max(0, Math.min(1, done));
                }
                elapsed = cluster.getElapsedTime();
            }

            entries.add(new CraftingCpuListEntry(serial, cpu.getAvailableStorage(), cpu.getCoProcessors(),
                    cpu.getName(), job, jobAmount, progress, elapsed));
        }
        entries.sort(CPU_COMPARATOR);
        return new CraftingCpuList(entries);
    }

    private int getOrAssignCpuSerial(ICraftingCPU cpu) {
        Integer serial = cpuSerialMap.get(cpu);
        if (serial == null) {
            serial = nextCpuSerial++;
            cpuSerialMap.put(cpu, serial);
        }
        return serial;
    }

    public void selectCpu(int serial) {
        if (isClient()) {
            this.selectedCpuSerial = serial;
            sendClientAction(ACTION_SELECT_CPU, serial);
        } else {
            ICraftingCPU newSelected = null;
            if (serial != -1) {
                for (ICraftingCPU cpu : lastCpuSet) {
                    Integer cpuSerial = cpuSerialMap.get(cpu);
                    if (cpuSerial != null && cpuSerial == serial) {
                        newSelected = cpu;
                        break;
                    }
                }
            }
            if (newSelected != selectedCpu) {
                setCPU(newSelected);
            }
        }
    }

    @Override
    public void cycleSelectedCPU(boolean forward) {
        List<CraftingCpuListEntry> cpus = cpuList.getCpus();
        if (cpus.isEmpty()) {
            return;
        }
        int index = -1;
        for (int i = 0; i < cpus.size(); i++) {
            if (cpus.get(i).getSerial() == selectedCpuSerial) {
                index = i;
            }
        }
        index += forward ? 1 : -1;
        if (index < 0) {
            index = cpus.size() - 1;
        } else if (index >= cpus.size()) {
            index = 0;
        }
        selectCpu(cpus.get(index).getSerial());
    }

    public static class CraftingCpuList implements PacketWritable {
        private final List<CraftingCpuListEntry> cpus;

        public CraftingCpuList(List<CraftingCpuListEntry> cpus) {
            this.cpus = cpus;
        }

        public CraftingCpuList(PacketBuffer data) {
            int count = data.readVarInt();
            List<CraftingCpuListEntry> result = new ArrayList<>(count);
            for (int i = 0; i < count; i++) {
                result.add(CraftingCpuListEntry.readFromPacket(data));
            }
            this.cpus = result;
        }

        public List<CraftingCpuListEntry> getCpus() {
            return cpus;
        }

        @Override
        public void writeToPacket(PacketBuffer data) {
            data.writeVarInt(cpus.size());
            for (CraftingCpuListEntry entry : cpus) {
                entry.writeToPacket(data);
            }
        }

        @Override
        public boolean equals(Object o) {
            return o instanceof CraftingCpuList && cpus.equals(((CraftingCpuList) o).cpus);
        }

        @Override
        public int hashCode() {
            return cpus.hashCode();
        }
    }

    public static class CraftingCpuListEntry {
        private final int serial;
        private final long storage;
        private final int coProcessors;
        private final ITextComponent name;
        private final ItemStack jobItem;
        private final long jobAmount;
        private final float progress;
        private final long elapsedTimeNanos;

        public CraftingCpuListEntry(int serial, long storage, int coProcessors, ITextComponent name,
                ItemStack jobItem, long jobAmount, float progress, long elapsedTimeNanos) {
            this.serial = serial;
            this.storage = storage;
            this.coProcessors = coProcessors;
            this.name = name;
            this.jobItem = jobItem;
            this.jobAmount = jobAmount;
            this.progress = progress;
            this.elapsedTimeNanos = elapsedTimeNanos;
        }

        public static CraftingCpuListEntry readFromPacket(PacketBuffer data) {
            int serial = data.readInt();
            long storage = data.readLong();
            int coProcessors = data.readInt();
            ITextComponent name = data.readBoolean() ? data.readTextComponent() : null;
            ItemStack jobItem = data.readItemStack();
            long jobAmount = data.readVarLong();
            float progress = data.readFloat();
            long elapsed = data.readVarLong();
            return new CraftingCpuListEntry(serial, storage, coProcessors, name, jobItem, jobAmount, progress,
                    elapsed);
        }

        public void writeToPacket(PacketBuffer data) {
            data.writeInt(serial);
            data.writeLong(storage);
            data.writeInt(coProcessors);
            data.writeBoolean(name != null);
            if (name != null) {
                data.writeTextComponent(name);
            }
            data.writeItemStack(jobItem);
            data.writeVarLong(jobAmount);
            data.writeFloat(progress);
            data.writeVarLong(elapsedTimeNanos);
        }

        public int getSerial() {
            return serial;
        }

        public long getStorage() {
            return storage;
        }

        public int getCoProcessors() {
            return coProcessors;
        }

        public ITextComponent getName() {
            return name;
        }

        public boolean hasJob() {
            return !jobItem.isEmpty();
        }

        public ItemStack getJobItem() {
            return jobItem;
        }

        public long getJobAmount() {
            return jobAmount;
        }

        public float getProgress() {
            return progress;
        }

        public long getElapsedTimeNanos() {
            return elapsedTimeNanos;
        }

        @Override
        public boolean equals(Object o) {
            if (this == o) {
                return true;
            }
            if (!(o instanceof CraftingCpuListEntry)) {
                return false;
            }
            CraftingCpuListEntry e = (CraftingCpuListEntry) o;
            return serial == e.serial && storage == e.storage && coProcessors == e.coProcessors
                    && Objects.equals(name, e.name) && ItemStack.areItemStacksEqual(jobItem, e.jobItem)
                    && jobAmount == e.jobAmount && Float.compare(progress, e.progress) == 0
                    && elapsedTimeNanos == e.elapsedTimeNanos;
        }

        @Override
        public int hashCode() {
            return Objects.hash(serial, storage, coProcessors, name, jobAmount, progress, elapsedTimeNanos);
        }
    }

}
