def bubble_sort(arr):
    """
    冒泡排序算法实现
    
    Args:
        arr: 待排序的列表
    
    Returns:
        排序后的列表
    """
    n = len(arr)
    # 创建数组副本以避免修改原数组
    sorted_arr = arr.copy()
    
    # 外层循环控制排序轮数
    for i in range(n):
        # 标记本轮是否发生交换
        swapped = False
        
        # 内层循环进行相邻元素比较和交换
        for j in range(0, n - i - 1):
            # 如果前一个元素大于后一个元素，则交换
            if sorted_arr[j] > sorted_arr[j + 1]:
                sorted_arr[j], sorted_arr[j + 1] = sorted_arr[j + 1], sorted_arr[j]
                swapped = True
        
        # 如果本轮没有发生交换，说明数组已经有序，可以提前结束
        if not swapped:
            break
    
    return sorted_arr


def bubble_sort_verbose(arr):
    """
    带详细过程输出的冒泡排序算法实现
    
    Args:
        arr: 待排序的列表
    
    Returns:
        排序后的列表
    """
    n = len(arr)
    sorted_arr = arr.copy()
    
    print(f"初始数组: {sorted_arr}")
    
    for i in range(n):
        swapped = False
        print(f"\n第 {i + 1} 轮排序:")
        
        for j in range(0, n - i - 1):
            print(f"  比较 {sorted_arr[j]} 和 {sorted_arr[j + 1]}", end="")
            
            if sorted_arr[j] > sorted_arr[j + 1]:
                sorted_arr[j], sorted_arr[j + 1] = sorted_arr[j + 1], sorted_arr[j]
                swapped = True
                print(f" -> 交换: {sorted_arr}")
            else:
                print(f" -> 不交换: {sorted_arr}")
        
        if not swapped:
            print(f"  本轮无交换，排序完成")
            break
        else:
            print(f"  第 {i + 1} 轮结束: {sorted_arr}")
    
    return sorted_arr


# 示例用法
if __name__ == "__main__":
    # 测试数据
    test_arrays = [
        [64, 34, 25, 12, 22, 11, 90],
        [5, 2, 8, 1, 9],
        [1, 2, 3, 4, 5],  # 已排序数组
        [5, 4, 3, 2, 1],  # 逆序数组
        [42],             # 单个元素
        []                # 空数组
    ]
    
    for i, arr in enumerate(test_arrays):
        print(f"\n{'='*50}")
        print(f"测试用例 {i + 1}: {arr}")
        
        # 使用标准冒泡排序
        sorted_arr = bubble_sort(arr)
        print(f"排序结果: {sorted_arr}")
        
        # 对于较短的数组，展示详细过程
        if len(arr) > 0 and len(arr) <= 6:
            print(f"\n详细排序过程:")
            bubble_sort_verbose(arr)