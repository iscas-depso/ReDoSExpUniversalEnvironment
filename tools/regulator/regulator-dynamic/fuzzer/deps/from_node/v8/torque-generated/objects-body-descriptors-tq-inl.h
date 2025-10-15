#ifndef V8_GEN_TORQUE_GENERATED_OBJECTS_BODY_DESCRIPTORS_TQ_INL_H_
#define V8_GEN_TORQUE_GENERATED_OBJECTS_BODY_DESCRIPTORS_TQ_INL_H_


#include "src/objects/objects-body-descriptors.h"

#include "torque-generated/class-definitions-tq.h"

#include "torque-generated/internal-class-definitions-tq.h"

#include "torque-generated/internal-class-definitions-tq-inl.h"
namespace v8 {
namespace internal {
class InternalClass::BodyDescriptor final : public BodyDescriptorBase {
 public:
  static bool IsValidSlot(Map map, HeapObject obj, int offset) {
    if (offset < HeapObject::kHeaderSize) return true;
    return offset >= InternalClass::kStartOfStrongFieldsOffset && offset < InternalClass::kEndOfStrongFieldsOffset;
  }

  template <typename ObjectVisitor>
  static inline void IterateBody(Map map, HeapObject obj, int object_size, ObjectVisitor* v) {
    if (InternalClass::kStartOfStrongFieldsOffset != InternalClass::kEndOfStrongFieldsOffset) {
      IteratePointers(obj, InternalClass::kStartOfStrongFieldsOffset, InternalClass::kEndOfStrongFieldsOffset, v);
    }
    if (InternalClass::kStartOfWeakFieldsOffset != InternalClass::kEndOfWeakFieldsOffset) {
      IterateCustomWeakPointers(obj, InternalClass::kStartOfWeakFieldsOffset, InternalClass::kEndOfWeakFieldsOffset, v);
    }
  }

  static inline int SizeOf(Map map, HeapObject raw_object) {
    InternalClass object = InternalClass::cast(raw_object);
    return InternalClass::SizeFor(object);
  }

};
class SmiPair::BodyDescriptor final : public BodyDescriptorBase {
 public:
  static bool IsValidSlot(Map map, HeapObject obj, int offset) {
    if (offset < HeapObject::kHeaderSize) return true;
    return offset >= SmiPair::kStartOfStrongFieldsOffset && offset < SmiPair::kEndOfStrongFieldsOffset;
  }

  template <typename ObjectVisitor>
  static inline void IterateBody(Map map, HeapObject obj, int object_size, ObjectVisitor* v) {
    if (SmiPair::kStartOfStrongFieldsOffset != SmiPair::kEndOfStrongFieldsOffset) {
      IteratePointers(obj, SmiPair::kStartOfStrongFieldsOffset, SmiPair::kEndOfStrongFieldsOffset, v);
    }
    if (SmiPair::kStartOfWeakFieldsOffset != SmiPair::kEndOfWeakFieldsOffset) {
      IterateCustomWeakPointers(obj, SmiPair::kStartOfWeakFieldsOffset, SmiPair::kEndOfWeakFieldsOffset, v);
    }
  }

  static inline int SizeOf(Map map, HeapObject raw_object) {
    SmiPair object = SmiPair::cast(raw_object);
    return SmiPair::SizeFor(object);
  }

};
class SmiBox::BodyDescriptor final : public BodyDescriptorBase {
 public:
  static bool IsValidSlot(Map map, HeapObject obj, int offset) {
    if (offset < HeapObject::kHeaderSize) return true;
    return offset >= SmiBox::kStartOfStrongFieldsOffset && offset < SmiBox::kEndOfStrongFieldsOffset;
  }

  template <typename ObjectVisitor>
  static inline void IterateBody(Map map, HeapObject obj, int object_size, ObjectVisitor* v) {
    if (SmiBox::kStartOfStrongFieldsOffset != SmiBox::kEndOfStrongFieldsOffset) {
      IteratePointers(obj, SmiBox::kStartOfStrongFieldsOffset, SmiBox::kEndOfStrongFieldsOffset, v);
    }
    if (SmiBox::kStartOfWeakFieldsOffset != SmiBox::kEndOfWeakFieldsOffset) {
      IterateCustomWeakPointers(obj, SmiBox::kStartOfWeakFieldsOffset, SmiBox::kEndOfWeakFieldsOffset, v);
    }
  }

  static inline int SizeOf(Map map, HeapObject raw_object) {
    SmiBox object = SmiBox::cast(raw_object);
    return SmiBox::SizeFor(object);
  }

};
class ExportedSubClassBase::BodyDescriptor final : public BodyDescriptorBase {
 public:
  static bool IsValidSlot(Map map, HeapObject obj, int offset) {
    if (offset < HeapObject::kHeaderSize) return true;
    return offset >= ExportedSubClassBase::kStartOfStrongFieldsOffset && offset < ExportedSubClassBase::kEndOfStrongFieldsOffset;
  }

  template <typename ObjectVisitor>
  static inline void IterateBody(Map map, HeapObject obj, int object_size, ObjectVisitor* v) {
    if (ExportedSubClassBase::kStartOfStrongFieldsOffset != ExportedSubClassBase::kEndOfStrongFieldsOffset) {
      IteratePointers(obj, ExportedSubClassBase::kStartOfStrongFieldsOffset, ExportedSubClassBase::kEndOfStrongFieldsOffset, v);
    }
    if (ExportedSubClassBase::kStartOfWeakFieldsOffset != ExportedSubClassBase::kEndOfWeakFieldsOffset) {
      IterateCustomWeakPointers(obj, ExportedSubClassBase::kStartOfWeakFieldsOffset, ExportedSubClassBase::kEndOfWeakFieldsOffset, v);
    }
  }

  static inline int SizeOf(Map map, HeapObject raw_object) {
    ExportedSubClassBase object = ExportedSubClassBase::cast(raw_object);
    return ExportedSubClassBase::SizeFor(object);
  }

};
class ExportedSubClass::BodyDescriptor final : public BodyDescriptorBase {
 public:
  static bool IsValidSlot(Map map, HeapObject obj, int offset) {
    if (ExportedSubClassBase::BodyDescriptor::IsValidSlot(map, obj, offset)) return true;
    return offset >= ExportedSubClass::kStartOfStrongFieldsOffset && offset < ExportedSubClass::kEndOfStrongFieldsOffset;
  }

  template <typename ObjectVisitor>
  static inline void IterateBody(Map map, HeapObject obj, int object_size, ObjectVisitor* v) {
    ExportedSubClassBase::BodyDescriptor::IterateBody(map, obj, object_size, v);
    if (ExportedSubClass::kStartOfStrongFieldsOffset != ExportedSubClass::kEndOfStrongFieldsOffset) {
      IteratePointers(obj, ExportedSubClass::kStartOfStrongFieldsOffset, ExportedSubClass::kEndOfStrongFieldsOffset, v);
    }
    if (ExportedSubClass::kStartOfWeakFieldsOffset != ExportedSubClass::kEndOfWeakFieldsOffset) {
      IterateCustomWeakPointers(obj, ExportedSubClass::kStartOfWeakFieldsOffset, ExportedSubClass::kEndOfWeakFieldsOffset, v);
    }
  }

  static inline int SizeOf(Map map, HeapObject raw_object) {
    ExportedSubClass object = ExportedSubClass::cast(raw_object);
    return ExportedSubClass::SizeFor(object);
  }

};
class InternalClassWithSmiElements::BodyDescriptor final : public BodyDescriptorBase {
 public:
  static bool IsValidSlot(Map map, HeapObject obj, int offset) {
    if (offset < FixedArrayBase::kHeaderSize) return true;
    return offset >= InternalClassWithSmiElements::kStartOfStrongFieldsOffset && offset < InternalClassWithSmiElements::kEndOfStrongFieldsOffset;
  }

  template <typename ObjectVisitor>
  static inline void IterateBody(Map map, HeapObject obj, int object_size, ObjectVisitor* v) {
    if (InternalClassWithSmiElements::kStartOfStrongFieldsOffset != InternalClassWithSmiElements::kEndOfStrongFieldsOffset) {
      IteratePointers(obj, InternalClassWithSmiElements::kStartOfStrongFieldsOffset, InternalClassWithSmiElements::kEndOfStrongFieldsOffset, v);
    }
    if (InternalClassWithSmiElements::kStartOfWeakFieldsOffset != InternalClassWithSmiElements::kEndOfWeakFieldsOffset) {
      IterateCustomWeakPointers(obj, InternalClassWithSmiElements::kStartOfWeakFieldsOffset, InternalClassWithSmiElements::kEndOfWeakFieldsOffset, v);
    }
    BodyDescriptorBase::IteratePointers(obj, InternalClassWithSmiElements::kEntriesOffset, InternalClassWithSmiElements::SizeFor(InternalClassWithSmiElements::cast(obj)), v);
  }

  static inline int SizeOf(Map map, HeapObject raw_object) {
    InternalClassWithSmiElements object = InternalClassWithSmiElements::cast(raw_object);
    return InternalClassWithSmiElements::SizeFor(object);
  }

};
class InternalClassWithStructElements::BodyDescriptor final : public BodyDescriptorBase {
 public:
  static bool IsValidSlot(Map map, HeapObject obj, int offset) {
    if (offset < HeapObject::kHeaderSize) return true;
    return offset >= InternalClassWithStructElements::kStartOfStrongFieldsOffset && offset < InternalClassWithStructElements::kEndOfStrongFieldsOffset;
  }

  template <typename ObjectVisitor>
  static inline void IterateBody(Map map, HeapObject obj, int object_size, ObjectVisitor* v) {
    if (InternalClassWithStructElements::kStartOfStrongFieldsOffset != InternalClassWithStructElements::kEndOfStrongFieldsOffset) {
      IteratePointers(obj, InternalClassWithStructElements::kStartOfStrongFieldsOffset, InternalClassWithStructElements::kEndOfStrongFieldsOffset, v);
    }
    if (InternalClassWithStructElements::kStartOfWeakFieldsOffset != InternalClassWithStructElements::kEndOfWeakFieldsOffset) {
      IterateCustomWeakPointers(obj, InternalClassWithStructElements::kStartOfWeakFieldsOffset, InternalClassWithStructElements::kEndOfWeakFieldsOffset, v);
    }
    BodyDescriptorBase::IteratePointers(obj, InternalClassWithStructElements::kEntriesOffset, InternalClassWithStructElements::SizeFor(InternalClassWithStructElements::cast(obj)), v);
  }

  static inline int SizeOf(Map map, HeapObject raw_object) {
    InternalClassWithStructElements object = InternalClassWithStructElements::cast(raw_object);
    return InternalClassWithStructElements::SizeFor(object);
  }

};
class SortState::BodyDescriptor final : public BodyDescriptorBase {
 public:
  static bool IsValidSlot(Map map, HeapObject obj, int offset) {
    if (offset < HeapObject::kHeaderSize) return true;
    return offset >= SortState::kStartOfStrongFieldsOffset && offset < SortState::kEndOfStrongFieldsOffset;
  }

  template <typename ObjectVisitor>
  static inline void IterateBody(Map map, HeapObject obj, int object_size, ObjectVisitor* v) {
    if (SortState::kStartOfStrongFieldsOffset != SortState::kEndOfStrongFieldsOffset) {
      IteratePointers(obj, SortState::kStartOfStrongFieldsOffset, SortState::kEndOfStrongFieldsOffset, v);
    }
    if (SortState::kStartOfWeakFieldsOffset != SortState::kEndOfWeakFieldsOffset) {
      IterateCustomWeakPointers(obj, SortState::kStartOfWeakFieldsOffset, SortState::kEndOfWeakFieldsOffset, v);
    }
  }

  static inline int SizeOf(Map map, HeapObject raw_object) {
    SortState object = SortState::cast(raw_object);
    return SortState::SizeFor(object);
  }

};
}  // namespace internal
}  // namespace v8
#endif  // V8_GEN_TORQUE_GENERATED_OBJECTS_BODY_DESCRIPTORS_TQ_INL_H_
