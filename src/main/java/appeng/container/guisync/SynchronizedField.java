package appeng.container.guisync;

import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodHandles;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.util.Objects;

import net.minecraft.network.PacketBuffer;
import net.minecraft.util.text.ITextComponent;

/**
 * This class is responsible for synchronizing Container-fields from server to client.
 */
public abstract class SynchronizedField<T> {

    private final Object source;
    protected final MethodHandle getter;
    protected final MethodHandle setter;
    protected T clientVersion;

    private SynchronizedField(Object source, Field field) {
        this.clientVersion = null;
        this.source = source;
        field.setAccessible(true);
        try {
            this.getter = MethodHandles.publicLookup().unreflectGetter(field);
            this.setter = MethodHandles.publicLookup().unreflectSetter(field);
        } catch (IllegalAccessException e) {
            throw new RuntimeException(
                    "Failed to get accessor for field " + field + ". Did you forget to make it public?");
        }
    }

    @SuppressWarnings("unchecked")
    private T getCurrentValue() {
        try {
            return (T) this.getter.invoke(source);
        } catch (Throwable throwable) {
            throw new RuntimeException(throwable);
        }
    }

    public boolean hasChanges() {
        return !Objects.equals(getCurrentValue(), this.clientVersion);
    }

    public final void write(PacketBuffer data) {
        T currentValue = getCurrentValue();
        this.clientVersion = currentValue;
        this.writeValue(data, currentValue);
    }

    public final void read(PacketBuffer data) {
        T value = readValue(data);
        try {
            setter.invoke(source, value);
        } catch (Throwable throwable) {
            throw new RuntimeException(throwable);
        }
    }

    protected abstract void writeValue(PacketBuffer data, T value);

    protected abstract T readValue(PacketBuffer data);

    public static SynchronizedField<?> create(Object source, Field field) {
        Class<?> fieldType = field.getType();

        if (fieldType.isAssignableFrom(ITextComponent.class)) {
            return new TextComponentField(source, field);
        } else if (fieldType == String.class) {
            return new StringField(source, field);
        } else if (fieldType == int.class || fieldType == Integer.class) {
            return new IntegerField(source, field);
        } else if (fieldType == long.class || fieldType == Long.class) {
            return new LongField(source, field);
        } else if (fieldType == boolean.class || fieldType == Boolean.class) {
            return new BooleanField(source, field);
        } else if (PacketWritable.class.isAssignableFrom(fieldType)) {
            return new PacketWritableField<>(source, field, fieldType);
        } else if (fieldType.isEnum()) {
            return createEnumField(source, field, fieldType.asSubclass(Enum.class));
        } else {
            throw new IllegalArgumentException("Cannot synchronize field " + field);
        }
    }

    private static <T extends Enum<T>> EnumField<T> createEnumField(Object source, Field field, Class<T> fieldType) {
        return new EnumField<>(source, field, fieldType.getEnumConstants());
    }

    private static class StringField extends SynchronizedField<String> {
        private StringField(Object source, Field field) {
            super(source, field);
        }

        @Override
        protected void writeValue(PacketBuffer data, String value) {
            data.writeString(value);
        }

        @Override
        protected String readValue(PacketBuffer data) {
            return data.readString();
        }
    }

    private static class IntegerField extends SynchronizedField<Integer> {
        private IntegerField(Object source, Field field) {
            super(source, field);
        }

        @Override
        protected void writeValue(PacketBuffer data, Integer value) {
            data.writeInt(value);
        }

        @Override
        protected Integer readValue(PacketBuffer data) {
            return data.readInt();
        }
    }

    private static class LongField extends SynchronizedField<Long> {
        private LongField(Object source, Field field) {
            super(source, field);
        }

        @Override
        protected void writeValue(PacketBuffer data, Long value) {
            data.writeLong(value);
        }

        @Override
        protected Long readValue(PacketBuffer data) {
            return data.readLong();
        }
    }

    private static class BooleanField extends SynchronizedField<Boolean> {
        private BooleanField(Object source, Field field) {
            super(source, field);
        }

        @Override
        protected void writeValue(PacketBuffer data, Boolean value) {
            data.writeBoolean(value);
        }

        @Override
        protected Boolean readValue(PacketBuffer data) {
            return data.readBoolean();
        }
    }

    private static class EnumField<T extends Enum<T>> extends SynchronizedField<T> {
        private final T[] values;

        private EnumField(Object source, Field field, T[] values) {
            super(source, field);
            this.values = values;
        }

        @Override
        protected void writeValue(PacketBuffer data, T value) {
            data.writeVarInt(value.ordinal());
        }

        @Override
        protected T readValue(PacketBuffer data) {
            int ordinal = data.readVarInt();
            return values[ordinal];
        }
    }

    private static class TextComponentField extends SynchronizedField<ITextComponent> {
        private TextComponentField(Object source, Field field) {
            super(source, field);
        }

        @Override
        protected void writeValue(PacketBuffer data, ITextComponent value) {
            if (value == null) {
                data.writeBoolean(false);
            } else {
                data.writeBoolean(true);
                data.writeTextComponent(value);
            }
        }

        @Override
        protected ITextComponent readValue(PacketBuffer data) {
            if (data.readBoolean()) {
                return data.readTextComponent();
            } else {
                return null;
            }
        }
    }

    private static class PacketWritableField<T extends PacketWritable> extends SynchronizedField<T> {
        private final Constructor<?> constructor;

        private PacketWritableField(Object source, Field field, Class<?> fieldType) {
            super(source, field);
            try {
                this.constructor = fieldType.getConstructor(PacketBuffer.class);
            } catch (NoSuchMethodException e) {
                throw new IllegalArgumentException(
                        "Cannot synchronize " + field + ": " + fieldType + " needs a public constructor(PacketBuffer)",
                        e);
            }
        }

        @Override
        protected void writeValue(PacketBuffer data, T value) {
            if (value == null) {
                data.writeBoolean(false);
            } else {
                data.writeBoolean(true);
                value.writeToPacket(data);
            }
        }

        @Override
        @SuppressWarnings("unchecked")
        protected T readValue(PacketBuffer data) {
            if (!data.readBoolean()) {
                return null;
            }
            try {
                return (T) constructor.newInstance(data);
            } catch (ReflectiveOperationException e) {
                throw new RuntimeException(e);
            }
        }
    }

}
