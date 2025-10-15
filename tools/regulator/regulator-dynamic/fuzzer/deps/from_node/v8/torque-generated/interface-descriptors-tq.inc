class ArrayEveryLoopContinuationDescriptor : public TorqueInterfaceDescriptor<8> {
  DECLARE_DESCRIPTOR_WITH_BASE(ArrayEveryLoopContinuationDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 8> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::AnyTagged(), MachineType::AnyTagged(), MachineType::TaggedPointer(), MachineType::AnyTagged(), MachineType::AnyTagged(), MachineType::AnyTagged()};
  }
};

class ArrayFilterLoopContinuationDescriptor : public TorqueInterfaceDescriptor<8> {
  DECLARE_DESCRIPTOR_WITH_BASE(ArrayFilterLoopContinuationDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 8> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::AnyTagged(), MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::AnyTagged(), MachineType::AnyTagged(), MachineType::AnyTagged()};
  }
};

class ArrayFindLoopContinuationDescriptor : public TorqueInterfaceDescriptor<6> {
  DECLARE_DESCRIPTOR_WITH_BASE(ArrayFindLoopContinuationDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 6> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::AnyTagged(), MachineType::TaggedPointer(), MachineType::AnyTagged(), MachineType::AnyTagged()};
  }
};

class ArrayFindIndexLoopContinuationDescriptor : public TorqueInterfaceDescriptor<6> {
  DECLARE_DESCRIPTOR_WITH_BASE(ArrayFindIndexLoopContinuationDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 6> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::AnyTagged(), MachineType::TaggedPointer(), MachineType::AnyTagged(), MachineType::AnyTagged()};
  }
};

class ArrayForEachLoopContinuationDescriptor : public TorqueInterfaceDescriptor<8> {
  DECLARE_DESCRIPTOR_WITH_BASE(ArrayForEachLoopContinuationDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 8> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::AnyTagged(), MachineType::AnyTagged(), MachineType::TaggedPointer(), MachineType::AnyTagged(), MachineType::AnyTagged(), MachineType::AnyTagged()};
  }
};

class LoadJoinElement_DictionaryElements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(LoadJoinElement_DictionaryElements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class LoadJoinElement_FastSmiOrObjectElements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(LoadJoinElement_FastSmiOrObjectElements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class LoadJoinElement_FastDoubleElements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(LoadJoinElement_FastDoubleElements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class ConvertToLocaleStringDescriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(ConvertToLocaleStringDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedPointer();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::AnyTagged(), MachineType::AnyTagged(), MachineType::AnyTagged()};
  }
};

class JoinStackPushDescriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(JoinStackPushDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedPointer();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer()};
  }
};

class JoinStackPopDescriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(JoinStackPopDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer()};
  }
};

class ArrayMapLoopContinuationDescriptor : public TorqueInterfaceDescriptor<7> {
  DECLARE_DESCRIPTOR_WITH_BASE(ArrayMapLoopContinuationDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 7> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::AnyTagged(), MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::AnyTagged(), MachineType::AnyTagged()};
  }
};

class ArrayReduceRightLoopContinuationDescriptor : public TorqueInterfaceDescriptor<6> {
  DECLARE_DESCRIPTOR_WITH_BASE(ArrayReduceRightLoopContinuationDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 6> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::AnyTagged(), MachineType::TaggedPointer(), MachineType::AnyTagged(), MachineType::AnyTagged()};
  }
};

class ArrayReduceLoopContinuationDescriptor : public TorqueInterfaceDescriptor<6> {
  DECLARE_DESCRIPTOR_WITH_BASE(ArrayReduceLoopContinuationDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 6> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::AnyTagged(), MachineType::TaggedPointer(), MachineType::AnyTagged(), MachineType::AnyTagged()};
  }
};

class ArraySomeLoopContinuationDescriptor : public TorqueInterfaceDescriptor<8> {
  DECLARE_DESCRIPTOR_WITH_BASE(ArraySomeLoopContinuationDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 8> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::AnyTagged(), MachineType::AnyTagged(), MachineType::TaggedPointer(), MachineType::AnyTagged(), MachineType::AnyTagged(), MachineType::AnyTagged()};
  }
};

class ToIntegerDescriptor : public TorqueInterfaceDescriptor<1> {
  DECLARE_DESCRIPTOR_WITH_BASE(ToIntegerDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 1> ParameterTypes() override {
    return {MachineType::AnyTagged()};
  }
};

class ToStringDescriptor : public TorqueInterfaceDescriptor<1> {
  DECLARE_DESCRIPTOR_WITH_BASE(ToStringDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedPointer();
  }
  std::array<MachineType, 1> ParameterTypes() override {
    return {MachineType::AnyTagged()};
  }
};

class FastCreateDataPropertyDescriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(FastCreateDataPropertyDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::AnyTagged(), MachineType::AnyTagged()};
  }
};

class CheckNumberInRangeDescriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(CheckNumberInRangeDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedPointer();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::AnyTagged(), MachineType::AnyTagged(), MachineType::AnyTagged()};
  }
};

class CheckSameObjectDescriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(CheckSameObjectDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedPointer();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::AnyTagged(), MachineType::AnyTagged()};
  }
};

class BigIntAddNoThrowDescriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(BigIntAddNoThrowDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer()};
  }
};

class BigIntAddDescriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(BigIntAddDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedPointer();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::AnyTagged(), MachineType::AnyTagged()};
  }
};

class BigIntSubtractNoThrowDescriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(BigIntSubtractNoThrowDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer()};
  }
};

class BigIntSubtractDescriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(BigIntSubtractDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedPointer();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::AnyTagged(), MachineType::AnyTagged()};
  }
};

class BigIntUnaryMinusDescriptor : public TorqueInterfaceDescriptor<1> {
  DECLARE_DESCRIPTOR_WITH_BASE(BigIntUnaryMinusDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedPointer();
  }
  std::array<MachineType, 1> ParameterTypes() override {
    return {MachineType::TaggedPointer()};
  }
};

class StringToListDescriptor : public TorqueInterfaceDescriptor<1> {
  DECLARE_DESCRIPTOR_WITH_BASE(StringToListDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedPointer();
  }
  std::array<MachineType, 1> ParameterTypes() override {
    return {MachineType::TaggedPointer()};
  }
};

class StringAddConvertLeftDescriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(StringAddConvertLeftDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedPointer();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::AnyTagged(), MachineType::TaggedPointer()};
  }
};

class StringAddConvertRightDescriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(StringAddConvertRightDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedPointer();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::AnyTagged()};
  }
};

class StringCharAtDescriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(StringCharAtDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedPointer();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class IncBlockCounterDescriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(IncBlockCounterDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedPointer();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedSigned()};
  }
};

class GetIteratorWithFeedbackDescriptor : public TorqueInterfaceDescriptor<4> {
  DECLARE_DESCRIPTOR_WITH_BASE(GetIteratorWithFeedbackDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 4> ParameterTypes() override {
    return {MachineType::AnyTagged(), MachineType::AnyTagged(), MachineType::AnyTagged(), MachineType::TaggedPointer()};
  }
};

class CallIteratorWithFeedbackDescriptor : public TorqueInterfaceDescriptor<4> {
  DECLARE_DESCRIPTOR_WITH_BASE(CallIteratorWithFeedbackDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 4> ParameterTypes() override {
    return {MachineType::AnyTagged(), MachineType::AnyTagged(), MachineType::TaggedSigned(), MachineType::TaggedPointer()};
  }
};

class CreateObjectWithoutPropertiesDescriptor : public TorqueInterfaceDescriptor<1> {
  DECLARE_DESCRIPTOR_WITH_BASE(CreateObjectWithoutPropertiesDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 1> ParameterTypes() override {
    return {MachineType::AnyTagged()};
  }
};

class FulfillPromiseDescriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(FulfillPromiseDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedPointer();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::AnyTagged()};
  }
};

class RejectPromiseDescriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(RejectPromiseDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::AnyTagged(), MachineType::TaggedPointer()};
  }
};

class NewPromiseCapabilityDescriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(NewPromiseCapabilityDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedPointer();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::AnyTagged(), MachineType::AnyTagged()};
  }
};

class PerformPromiseThenDescriptor : public TorqueInterfaceDescriptor<4> {
  DECLARE_DESCRIPTOR_WITH_BASE(PerformPromiseThenDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 4> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::TaggedPointer()};
  }
};

class PromiseFulfillReactionJobDescriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(PromiseFulfillReactionJobDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::AnyTagged(), MachineType::TaggedPointer(), MachineType::TaggedPointer()};
  }
};

class PromiseRejectReactionJobDescriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(PromiseRejectReactionJobDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::AnyTagged(), MachineType::TaggedPointer(), MachineType::TaggedPointer()};
  }
};

class PromiseResolveDescriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(PromiseResolveDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::AnyTagged()};
  }
};

class ResolvePromiseDescriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(ResolvePromiseDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::AnyTagged()};
  }
};

class PromiseResolveThenableJobDescriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(PromiseResolveThenableJobDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::AnyTagged()};
  }
};

class ProxyDeletePropertyDescriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(ProxyDeletePropertyDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::TaggedSigned()};
  }
};

class ProxyGetPropertyDescriptor : public TorqueInterfaceDescriptor<4> {
  DECLARE_DESCRIPTOR_WITH_BASE(ProxyGetPropertyDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 4> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::AnyTagged(), MachineType::TaggedSigned()};
  }
};

class ProxyGetPrototypeOfDescriptor : public TorqueInterfaceDescriptor<1> {
  DECLARE_DESCRIPTOR_WITH_BASE(ProxyGetPrototypeOfDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 1> ParameterTypes() override {
    return {MachineType::TaggedPointer()};
  }
};

class ProxyHasPropertyDescriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(ProxyHasPropertyDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer()};
  }
};

class ProxyIsExtensibleDescriptor : public TorqueInterfaceDescriptor<1> {
  DECLARE_DESCRIPTOR_WITH_BASE(ProxyIsExtensibleDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 1> ParameterTypes() override {
    return {MachineType::TaggedPointer()};
  }
};

class ProxyPreventExtensionsDescriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(ProxyPreventExtensionsDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer()};
  }
};

class ProxySetPropertyDescriptor : public TorqueInterfaceDescriptor<4> {
  DECLARE_DESCRIPTOR_WITH_BASE(ProxySetPropertyDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 4> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::AnyTagged(), MachineType::AnyTagged()};
  }
};

class ProxySetPrototypeOfDescriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(ProxySetPrototypeOfDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::TaggedPointer()};
  }
};

class RegExpPrototypeExecSlowDescriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(RegExpPrototypeExecSlowDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer()};
  }
};

class RegExpMatchFastDescriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(RegExpMatchFastDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer()};
  }
};

class RegExpReplaceDescriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(RegExpReplaceDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedPointer();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::AnyTagged()};
  }
};

class RegExpSearchFastDescriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(RegExpSearchFastDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer()};
  }
};

class RegExpSplitDescriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(RegExpSplitDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::AnyTagged()};
  }
};

class RegExpPrototypeTestFastDescriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(RegExpPrototypeTestFastDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer()};
  }
};

class CreateHTMLDescriptor : public TorqueInterfaceDescriptor<5> {
  DECLARE_DESCRIPTOR_WITH_BASE(CreateHTMLDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedPointer();
  }
  std::array<MachineType, 5> ParameterTypes() override {
    return {MachineType::AnyTagged(), MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::AnyTagged()};
  }
};

class StringRepeatDescriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(StringRepeatDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedPointer();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedSigned()};
  }
};

class CreateTypedArrayDescriptor : public TorqueInterfaceDescriptor<5> {
  DECLARE_DESCRIPTOR_WITH_BASE(CreateTypedArrayDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedPointer();
  }
  std::array<MachineType, 5> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::AnyTagged(), MachineType::AnyTagged(), MachineType::AnyTagged()};
  }
};

class TypedArrayMergeSortDescriptor : public TorqueInterfaceDescriptor<6> {
  DECLARE_DESCRIPTOR_WITH_BASE(TypedArrayMergeSortDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 6> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value, MachineTypeOf<UintPtrT>::value, MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::TaggedPointer()};
  }
};

class GenericBuiltinTest_JSAny_0Descriptor : public TorqueInterfaceDescriptor<1> {
  DECLARE_DESCRIPTOR_WITH_BASE(GenericBuiltinTest_JSAny_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 1> ParameterTypes() override {
    return {MachineType::AnyTagged()};
  }
};

class TestHelperPlus1Descriptor : public TorqueInterfaceDescriptor<1> {
  DECLARE_DESCRIPTOR_WITH_BASE(TestHelperPlus1Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 1> ParameterTypes() override {
    return {MachineType::TaggedSigned()};
  }
};

class TestHelperPlus2Descriptor : public TorqueInterfaceDescriptor<1> {
  DECLARE_DESCRIPTOR_WITH_BASE(TestHelperPlus2Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 1> ParameterTypes() override {
    return {MachineType::TaggedSigned()};
  }
};

class NewSmiBoxDescriptor : public TorqueInterfaceDescriptor<1> {
  DECLARE_DESCRIPTOR_WITH_BASE(NewSmiBoxDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedPointer();
  }
  std::array<MachineType, 1> ParameterTypes() override {
    return {MachineType::TaggedSigned()};
  }
};

class Load_FastSmiElements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(Load_FastSmiElements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedSigned()};
  }
};

class Load_FastObjectElements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(Load_FastObjectElements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedSigned()};
  }
};

class Load_FastDoubleElements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(Load_FastDoubleElements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedSigned()};
  }
};

class Store_FastSmiElements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(Store_FastSmiElements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedSigned(), MachineType::AnyTagged()};
  }
};

class Store_FastObjectElements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(Store_FastObjectElements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedSigned(), MachineType::AnyTagged()};
  }
};

class Store_FastDoubleElements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(Store_FastDoubleElements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedSigned(), MachineType::AnyTagged()};
  }
};

class Delete_FastSmiElements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(Delete_FastSmiElements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedSigned()};
  }
};

class Delete_FastObjectElements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(Delete_FastObjectElements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedSigned()};
  }
};

class Delete_FastDoubleElements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(Delete_FastDoubleElements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedSigned()};
  }
};

class SortCompareDefaultDescriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(SortCompareDefaultDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::AnyTagged(), MachineType::AnyTagged(), MachineType::AnyTagged()};
  }
};

class SortCompareUserFnDescriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(SortCompareUserFnDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::AnyTagged(), MachineType::AnyTagged(), MachineType::AnyTagged()};
  }
};

class CanUseSameAccessor_GenericElementsAccessor_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(CanUseSameAccessor_GenericElementsAccessor_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedPointer();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::AnyTagged()};
  }
};

class CopyDescriptor : public TorqueInterfaceDescriptor<5> {
  DECLARE_DESCRIPTOR_WITH_BASE(CopyDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 5> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedSigned(), MachineType::TaggedPointer(), MachineType::TaggedSigned(), MachineType::TaggedSigned()};
  }
};

class MergeAtDescriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(MergeAtDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedSigned()};
  }
};

class GallopLeftDescriptor : public TorqueInterfaceDescriptor<6> {
  DECLARE_DESCRIPTOR_WITH_BASE(GallopLeftDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 6> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::AnyTagged(), MachineType::TaggedSigned(), MachineType::TaggedSigned(), MachineType::TaggedSigned()};
  }
};

class GallopRightDescriptor : public TorqueInterfaceDescriptor<6> {
  DECLARE_DESCRIPTOR_WITH_BASE(GallopRightDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 6> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::AnyTagged(), MachineType::TaggedSigned(), MachineType::TaggedSigned(), MachineType::TaggedSigned()};
  }
};

class ArrayTimSortDescriptor : public TorqueInterfaceDescriptor<1> {
  DECLARE_DESCRIPTOR_WITH_BASE(ArrayTimSortDescriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 1> ParameterTypes() override {
    return {MachineType::TaggedPointer()};
  }
};

class LoadJoinElement_GenericElementsAccessor_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(LoadJoinElement_GenericElementsAccessor_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class LoadJoinTypedElement_Int32Elements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(LoadJoinTypedElement_Int32Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class LoadJoinTypedElement_Float32Elements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(LoadJoinTypedElement_Float32Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class LoadJoinTypedElement_Float64Elements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(LoadJoinTypedElement_Float64Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class LoadJoinTypedElement_Uint8ClampedElements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(LoadJoinTypedElement_Uint8ClampedElements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class LoadJoinTypedElement_BigUint64Elements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(LoadJoinTypedElement_BigUint64Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class LoadJoinTypedElement_BigInt64Elements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(LoadJoinTypedElement_BigInt64Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class LoadJoinTypedElement_Uint8Elements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(LoadJoinTypedElement_Uint8Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class LoadJoinTypedElement_Int8Elements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(LoadJoinTypedElement_Int8Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class LoadJoinTypedElement_Uint16Elements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(LoadJoinTypedElement_Uint16Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class LoadJoinTypedElement_Int16Elements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(LoadJoinTypedElement_Int16Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class LoadJoinTypedElement_Uint32Elements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(LoadJoinTypedElement_Uint32Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class GenericBuiltinTest_Smi_0Descriptor : public TorqueInterfaceDescriptor<1> {
  DECLARE_DESCRIPTOR_WITH_BASE(GenericBuiltinTest_Smi_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 1> ParameterTypes() override {
    return {MachineType::TaggedSigned()};
  }
};

class CanUseSameAccessor_FastDoubleElements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(CanUseSameAccessor_FastDoubleElements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedPointer();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::AnyTagged()};
  }
};

class CanUseSameAccessor_FastSmiElements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(CanUseSameAccessor_FastSmiElements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedPointer();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::AnyTagged()};
  }
};

class CanUseSameAccessor_FastObjectElements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(CanUseSameAccessor_FastObjectElements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedPointer();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedPointer(), MachineType::AnyTagged()};
  }
};

class Load_GenericElementsAccessor_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(Load_GenericElementsAccessor_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedSigned()};
  }
};

class Store_GenericElementsAccessor_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(Store_GenericElementsAccessor_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedSigned(), MachineType::AnyTagged()};
  }
};

class Delete_GenericElementsAccessor_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(Delete_GenericElementsAccessor_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineType::TaggedSigned()};
  }
};

class LoadTypedElement_Int32Elements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(LoadTypedElement_Int32Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class StoreTypedElementNumeric_Int32Elements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(StoreTypedElementNumeric_Int32Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value, MachineType::AnyTagged()};
  }
};

class StoreTypedElementJSAny_Int32Elements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(StoreTypedElementJSAny_Int32Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value, MachineType::AnyTagged()};
  }
};

class LoadTypedElement_Float32Elements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(LoadTypedElement_Float32Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class StoreTypedElementNumeric_Float32Elements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(StoreTypedElementNumeric_Float32Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value, MachineType::AnyTagged()};
  }
};

class StoreTypedElementJSAny_Float32Elements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(StoreTypedElementJSAny_Float32Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value, MachineType::AnyTagged()};
  }
};

class LoadTypedElement_Float64Elements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(LoadTypedElement_Float64Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class StoreTypedElementNumeric_Float64Elements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(StoreTypedElementNumeric_Float64Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value, MachineType::AnyTagged()};
  }
};

class StoreTypedElementJSAny_Float64Elements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(StoreTypedElementJSAny_Float64Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value, MachineType::AnyTagged()};
  }
};

class LoadTypedElement_Uint8ClampedElements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(LoadTypedElement_Uint8ClampedElements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class StoreTypedElementNumeric_Uint8ClampedElements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(StoreTypedElementNumeric_Uint8ClampedElements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value, MachineType::AnyTagged()};
  }
};

class StoreTypedElementJSAny_Uint8ClampedElements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(StoreTypedElementJSAny_Uint8ClampedElements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value, MachineType::AnyTagged()};
  }
};

class LoadTypedElement_BigUint64Elements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(LoadTypedElement_BigUint64Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class StoreTypedElementNumeric_BigUint64Elements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(StoreTypedElementNumeric_BigUint64Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value, MachineType::AnyTagged()};
  }
};

class StoreTypedElementJSAny_BigUint64Elements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(StoreTypedElementJSAny_BigUint64Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value, MachineType::AnyTagged()};
  }
};

class LoadTypedElement_BigInt64Elements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(LoadTypedElement_BigInt64Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class StoreTypedElementNumeric_BigInt64Elements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(StoreTypedElementNumeric_BigInt64Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value, MachineType::AnyTagged()};
  }
};

class StoreTypedElementJSAny_BigInt64Elements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(StoreTypedElementJSAny_BigInt64Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value, MachineType::AnyTagged()};
  }
};

class LoadTypedElement_Uint8Elements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(LoadTypedElement_Uint8Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class StoreTypedElementNumeric_Uint8Elements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(StoreTypedElementNumeric_Uint8Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value, MachineType::AnyTagged()};
  }
};

class StoreTypedElementJSAny_Uint8Elements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(StoreTypedElementJSAny_Uint8Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value, MachineType::AnyTagged()};
  }
};

class LoadTypedElement_Int8Elements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(LoadTypedElement_Int8Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class StoreTypedElementNumeric_Int8Elements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(StoreTypedElementNumeric_Int8Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value, MachineType::AnyTagged()};
  }
};

class StoreTypedElementJSAny_Int8Elements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(StoreTypedElementJSAny_Int8Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value, MachineType::AnyTagged()};
  }
};

class LoadTypedElement_Uint16Elements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(LoadTypedElement_Uint16Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class StoreTypedElementNumeric_Uint16Elements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(StoreTypedElementNumeric_Uint16Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value, MachineType::AnyTagged()};
  }
};

class StoreTypedElementJSAny_Uint16Elements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(StoreTypedElementJSAny_Uint16Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value, MachineType::AnyTagged()};
  }
};

class LoadTypedElement_Int16Elements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(LoadTypedElement_Int16Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class StoreTypedElementNumeric_Int16Elements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(StoreTypedElementNumeric_Int16Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value, MachineType::AnyTagged()};
  }
};

class StoreTypedElementJSAny_Int16Elements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(StoreTypedElementJSAny_Int16Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value, MachineType::AnyTagged()};
  }
};

class LoadTypedElement_Uint32Elements_0Descriptor : public TorqueInterfaceDescriptor<2> {
  DECLARE_DESCRIPTOR_WITH_BASE(LoadTypedElement_Uint32Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::AnyTagged();
  }
  std::array<MachineType, 2> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value};
  }
};

class StoreTypedElementNumeric_Uint32Elements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(StoreTypedElementNumeric_Uint32Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value, MachineType::AnyTagged()};
  }
};

class StoreTypedElementJSAny_Uint32Elements_0Descriptor : public TorqueInterfaceDescriptor<3> {
  DECLARE_DESCRIPTOR_WITH_BASE(StoreTypedElementJSAny_Uint32Elements_0Descriptor, TorqueInterfaceDescriptor)
  MachineType ReturnType() override {
    return MachineType::TaggedSigned();
  }
  std::array<MachineType, 3> ParameterTypes() override {
    return {MachineType::TaggedPointer(), MachineTypeOf<UintPtrT>::value, MachineType::AnyTagged()};
  }
};

