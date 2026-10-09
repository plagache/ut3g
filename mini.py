from tinygrad import Tensor, Device, dtypes

# print(Device.DEFAULT)
#
# print("\nPart 1 - Tensor - uOPS - Lazy\n")
#
# t = Tensor([1, 2, 3, 4])
#
# print(f"{t.device == Device.DEFAULT = }")
# print(f"{t.dtype == dtypes.int = }")
# print(f"{t.shape == (4,) = }")
# print(f"{t = }")
# print(f"{t.uop = }")
#
# # Before its a copy
# t.realize()
# # After its a buffer
# print(f"{t.uop = }")
#
# # Compute
# t_times_2 = t * 2
# print(f"{t_times_2.uop = }")
# print(f"{t_times_2.tolist() == [2, 4, 6, 8] = }")
# print(f"{t_times_2.uop = }")
#
# # UOPs are both immutable and globally unique, leading to elegant computational deduplication
# # No recompute
# A = t * 4
# B = t * 4
#
# # Different Python objects
# print(f"{A is not B = }")
#
# # Same computational specification
# print(f"{A.uop is B.uop = }")
# print(f"{A.uop = }")
#
# A.realize()
#
# # Both tensors now point to the same realized buffer
# print(f"{A.uop is B.uop = }")
# print(f"{A.uop = }")
#
# print(f"{B.tolist() = }")

print("\nPart 2 - Autograd\n")

x = Tensor([2.0])
y = x**2 + 3*x + 1
loss = y.sum()

print(x.item())
print(y.item())

loss.backward()
print(x.grad.item())

# Tinygrad calculate the gradient by following the chain rule
# you can look it with the base AST of the VIZ=1

# print("\nPart X - Scheduling - Rangify\n")
# print("\nPart X - Lowering - Get an executable for each kernel\n")
# print("\nPart X - Rendering - Compilation\n")
