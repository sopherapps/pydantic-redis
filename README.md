# pydantic-redis

[![PyPI version](https://badge.fury.io/py/pydantic-redis.svg)](https://badge.fury.io/py/pydantic-redis) ![CI](https://github.com/sopherapps/pydantic-redis/actions/workflows/ci.yml/badge.svg)

A simple declarative ORM for Redis

---

**Documentation:** [https://sopherapps.github.io/pydantic-redis](https://sopherapps.github.io/pydantic-redis)

**Source Code:** [https://github.com/sopherapps/pydantic-redis](https://github.com/sopherapps/pydantic-redis)

--- 

Most Notable Features are:

- Define business domain objects as [pydantic](https://github.com/samuelcolvin/pydantic/) and automatically get ability
  to save them as is in [redis](https://pypi.org/project/redis/) with an intuitive API of `insert`, `update`, `delete`,
  `select`
- Maintain simple relationships between domain objects by simply nesting them either as single objects or lists, or tuples.
  Any direct or indirect update to a nested object will automatically reflect in all parent objects that have it nested in
  them when queried again from redis.
- Both synchronous and asynchronous APIs available.

## Benchmarks

### <v0.5

On an average PC ~16GB RAM, i7 Core

```
-------------------------------------------------- benchmark: 22 tests --------------------------------------------------
Name (time in us)                                                Mean                 Min                   Max          
-------------------------------------------------------------------------------------------------------------------------
benchmark_select_columns_for_one_id[redis_store-book2]       124.2687 (1.00)     115.4530 (1.0)        331.8030 (1.26)   
benchmark_select_columns_for_one_id[redis_store-book0]       123.7213 (1.0)      115.6680 (1.00)       305.7170 (1.16)   
benchmark_select_columns_for_one_id[redis_store-book3]       124.4495 (1.01)     115.9580 (1.00)       263.4370 (1.0)    
benchmark_select_columns_for_one_id[redis_store-book1]       124.8431 (1.01)     117.4770 (1.02)       310.3140 (1.18)   
benchmark_select_columns_for_some_items[redis_store]         128.0657 (1.04)     118.6380 (1.03)       330.2680 (1.25)   
benchmark_delete[redis_store-Wuthering Heights]              131.8713 (1.07)     125.9920 (1.09)       328.9660 (1.25)   
benchmark_bulk_delete[redis_store]                           148.6963 (1.20)     142.3190 (1.23)       347.4750 (1.32)   
benchmark_select_all_for_one_id[redis_store-book3]           211.6941 (1.71)     195.6520 (1.69)       422.8840 (1.61)   
benchmark_select_all_for_one_id[redis_store-book2]           212.3612 (1.72)     195.9020 (1.70)       447.4910 (1.70)   
benchmark_select_all_for_one_id[redis_store-book1]           212.9524 (1.72)     197.7530 (1.71)       423.3030 (1.61)   
benchmark_select_all_for_one_id[redis_store-book0]           214.9924 (1.74)     198.8280 (1.72)       402.6310 (1.53)   
benchmark_select_columns_paginated[redis_store]              227.9248 (1.84)     211.0610 (1.83)       425.8390 (1.62)   
benchmark_select_some_items[redis_store]                     297.5700 (2.41)     271.1510 (2.35)       572.1220 (2.17)   
benchmark_select_default_paginated[redis_store]              301.7495 (2.44)     282.6500 (2.45)       490.3450 (1.86)   
benchmark_select_columns[redis_store]                        316.2119 (2.56)     290.6110 (2.52)       578.0310 (2.19)   
benchmark_update[redis_store-Wuthering Heights-data0]        346.5816 (2.80)     304.5420 (2.64)       618.0250 (2.35)   
benchmark_single_insert[redis_store-book2]                   378.0613 (3.06)     337.8070 (2.93)       616.4930 (2.34)   
benchmark_single_insert[redis_store-book0]                   396.6513 (3.21)     347.1000 (3.01)       696.1350 (2.64)   
benchmark_single_insert[redis_store-book3]                   395.9082 (3.20)     361.0980 (3.13)       623.8630 (2.37)   
benchmark_single_insert[redis_store-book1]                   401.1377 (3.24)     363.5890 (3.15)       610.4400 (2.32)   
benchmark_select_default[redis_store]                        498.4673 (4.03)     428.1350 (3.71)       769.7640 (2.92)   
benchmark_bulk_insert[redis_store]                         1,025.0436 (8.29)     962.2230 (8.33)     1,200.3840 (4.56)   
-------------------------------------------------------------------------------------------------------------------------
```

# >v0.5 (with pydantic v2)

```
------------------------------------------------ benchmark: 22 tests ------------------------------------------------
Name (time in us)                                              Mean                 Min                 Max          
---------------------------------------------------------------------------------------------------------------------
benchmark_delete[redis_store-Wuthering Heights]            116.4282 (1.0)      103.9220 (1.0)      366.6500 (1.0)    
benchmark_bulk_delete[redis_store]                         125.1484 (1.07)     110.2590 (1.06)     393.1860 (1.07)   
benchmark_select_columns_for_one_id[redis_store-book0]     176.7461 (1.52)     151.4150 (1.46)     484.4690 (1.32)   
benchmark_select_columns_for_one_id[redis_store-book3]     175.1838 (1.50)     152.3430 (1.47)     443.8120 (1.21)   
benchmark_select_columns_for_one_id[redis_store-book1]     176.9439 (1.52)     152.9350 (1.47)     464.4280 (1.27)   
benchmark_select_columns_for_one_id[redis_store-book2]     176.7885 (1.52)     153.0280 (1.47)     520.9390 (1.42)   
benchmark_select_all_for_one_id[redis_store-book0]         198.9879 (1.71)     173.8040 (1.67)     527.0550 (1.44)   
benchmark_select_all_for_one_id[redis_store-book1]         199.1717 (1.71)     175.8920 (1.69)     461.5000 (1.26)   
benchmark_select_all_for_one_id[redis_store-book2]         197.1996 (1.69)     177.9590 (1.71)     473.8830 (1.29)   
benchmark_select_all_for_one_id[redis_store-book3]         198.1436 (1.70)     178.1040 (1.71)     493.0560 (1.34)   
benchmark_select_columns_for_some_items[redis_store]       230.9837 (1.98)     209.6070 (2.02)     441.7680 (1.20)   
benchmark_select_columns_paginated[redis_store]            242.5208 (2.08)     212.4460 (2.04)     512.9250 (1.40)   
benchmark_update[redis_store-Wuthering Heights-data0]      253.0142 (2.17)     223.0690 (2.15)     548.3980 (1.50)   
benchmark_single_insert[redis_store-book2]                 287.5952 (2.47)     246.2610 (2.37)     593.2120 (1.62)   
benchmark_select_some_items[redis_store]                   274.5612 (2.36)     248.9740 (2.40)     539.6020 (1.47)   
benchmark_select_default_paginated[redis_store]            280.0070 (2.40)     254.9000 (2.45)     587.5320 (1.60)   
benchmark_single_insert[redis_store-book3]                 293.2912 (2.52)     256.2000 (2.47)     523.5340 (1.43)   
benchmark_single_insert[redis_store-book1]                 299.4127 (2.57)     258.5760 (2.49)     564.0550 (1.54)   
benchmark_single_insert[redis_store-book0]                 293.0470 (2.52)     261.1910 (2.51)     590.2880 (1.61)   
benchmark_select_columns[redis_store]                      347.7573 (2.99)     313.4880 (3.02)     624.8470 (1.70)   
benchmark_select_default[redis_store]                      454.2192 (3.90)     398.2550 (3.83)     775.3050 (2.11)   
benchmark_bulk_insert[redis_store]                         721.2247 (6.19)     673.9940 (6.49)     958.1200 (2.61)   
---------------------------------------------------------------------------------------------------------------------
```

# >=v0.7 (with deeply nested models)

```
------------------------------------------------- benchmark: 22 tests -------------------------------------------------
Name (time in us)                                              Mean                 Min                   Max          
-----------------------------------------------------------------------------------------------------------------------
benchmark_delete[redis_store-Wuthering Heights]            123.2946 (1.02)     107.9690 (1.0)        502.6140 (1.33)   
benchmark_bulk_delete[redis_store]                         120.5815 (1.0)      111.9320 (1.04)       378.8660 (1.0)    
benchmark_select_columns_for_one_id[redis_store-book2]     208.2612 (1.73)     180.4660 (1.67)       470.9860 (1.24)   
benchmark_select_columns_for_one_id[redis_store-book1]     207.9143 (1.72)     180.6440 (1.67)       489.6890 (1.29)   
benchmark_select_columns_for_one_id[redis_store-book0]     204.2471 (1.69)     183.4360 (1.70)       485.2500 (1.28)   
benchmark_select_columns_for_one_id[redis_store-book3]     209.5764 (1.74)     189.5780 (1.76)       462.5650 (1.22)   
benchmark_select_all_for_one_id[redis_store-book0]         226.4569 (1.88)     207.4920 (1.92)       499.9470 (1.32)   
benchmark_select_all_for_one_id[redis_store-book3]         241.5488 (2.00)     210.5230 (1.95)       504.5150 (1.33)   
benchmark_select_all_for_one_id[redis_store-book1]         234.4014 (1.94)     210.6420 (1.95)       501.2470 (1.32)   
benchmark_select_all_for_one_id[redis_store-book2]         228.9277 (1.90)     212.0090 (1.96)       509.5740 (1.34)   
benchmark_update[redis_store-Wuthering Heights-data0]      276.3908 (2.29)     238.3390 (2.21)       704.9450 (1.86)   
benchmark_single_insert[redis_store-book3]                 311.0476 (2.58)     262.2940 (2.43)       589.3940 (1.56)   
benchmark_select_columns_for_some_items[redis_store]       291.2779 (2.42)     266.0960 (2.46)       564.3510 (1.49)   
benchmark_select_columns_paginated[redis_store]            300.4108 (2.49)     269.4740 (2.50)       552.8510 (1.46)   
benchmark_single_insert[redis_store-book1]                 304.5771 (2.53)     274.1740 (2.54)       547.5210 (1.45)   
benchmark_single_insert[redis_store-book2]                 317.2681 (2.63)     275.6170 (2.55)       641.5440 (1.69)   
benchmark_single_insert[redis_store-book0]                 313.0004 (2.60)     277.3190 (2.57)       558.2160 (1.47)   
benchmark_select_some_items[redis_store]                   343.2569 (2.85)     311.9140 (2.89)       624.6600 (1.65)   
benchmark_select_default_paginated[redis_store]            359.8463 (2.98)     325.8310 (3.02)       623.2360 (1.65)   
benchmark_select_columns[redis_store]                      486.6047 (4.04)     429.3250 (3.98)       867.8780 (2.29)   
benchmark_select_default[redis_store]                      631.3835 (5.24)     584.7630 (5.42)     1,033.5990 (2.73)   
benchmark_bulk_insert[redis_store]                         761.0832 (6.31)     724.1240 (6.71)     1,034.2950 (2.73)   
-----------------------------------------------------------------------------------------------------------------------
```

## Contributions

Contributions are welcome. The docs have to maintained, the code has to be made cleaner, more idiomatic and faster,
and there might be need for someone else to take over this repo in case I move on to other things. It happens!

When you are ready, look at the [CONTRIBUTIONS GUIDELINES](./CONTRIBUTING.md)

## License

Copyright (c) 2020 [Martin Ahindura](https://github.com/Tinitto) Licensed under the [MIT License](./LICENSE)

## Gratitude

> "There is no condemnation now for those who live in union with Christ Jesus.
> For the law of the Spirit, which brings us life in union with Christ Jesus,
> has set me free from the law of sin and death"
>
> -- Romans 8: 1-2

All glory be to God

<a href="https://www.buymeacoffee.com/martinahinJ" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>
