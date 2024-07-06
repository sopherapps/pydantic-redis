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

# >=v0.7 (with fully-fledged nested models)

```
--------------------------------------------------- benchmark: 22 tests ----------------------------------------------------
Name (time in us)                                                   Mean                 Min                   Max          
----------------------------------------------------------------------------------------------------------------------------
test_benchmark_delete[redis_store-Wuthering Heights]            124.5440 (1.01)     109.3710 (1.0)        579.7810 (1.39)   
test_benchmark_bulk_delete[redis_store]                         122.9285 (1.0)      113.7120 (1.04)       492.2730 (1.18)   
test_benchmark_select_columns_for_one_id[redis_store-book1]     182.3891 (1.48)     154.9150 (1.42)       441.2820 (1.06)   
test_benchmark_select_columns_for_one_id[redis_store-book2]     183.2679 (1.49)     156.6830 (1.43)       462.6000 (1.11)   
test_benchmark_select_columns_for_one_id[redis_store-book0]     181.6972 (1.48)     157.2330 (1.44)       459.2930 (1.10)   
test_benchmark_select_columns_for_one_id[redis_store-book3]     183.0834 (1.49)     160.1250 (1.46)       416.8570 (1.0)    
test_benchmark_select_all_for_one_id[redis_store-book1]         203.9491 (1.66)     183.3080 (1.68)       469.4700 (1.13)   
test_benchmark_select_all_for_one_id[redis_store-book2]         206.7124 (1.68)     184.1920 (1.68)       490.6700 (1.18)   
test_benchmark_select_all_for_one_id[redis_store-book0]         207.3341 (1.69)     184.2210 (1.68)       443.9260 (1.06)   
test_benchmark_select_all_for_one_id[redis_store-book3]         210.6874 (1.71)     185.0600 (1.69)       696.9330 (1.67)   
test_benchmark_select_columns_for_some_items[redis_store]       236.5783 (1.92)     215.7490 (1.97)       496.0540 (1.19)   
test_benchmark_select_columns_paginated[redis_store]            248.5335 (2.02)     218.3450 (2.00)       522.1270 (1.25)   
test_benchmark_update[redis_store-Wuthering Heights-data0]      282.1803 (2.30)     239.5410 (2.19)       541.5220 (1.30)   
test_benchmark_select_some_items[redis_store]                   298.2036 (2.43)     264.0860 (2.41)       599.3010 (1.44)   
test_benchmark_single_insert[redis_store-book0]                 316.0245 (2.57)     269.8110 (2.47)       596.0940 (1.43)   
test_benchmark_single_insert[redis_store-book2]                 314.1899 (2.56)     270.9780 (2.48)       560.5280 (1.34)   
test_benchmark_select_default_paginated[redis_store]            305.2798 (2.48)     277.8170 (2.54)       550.5110 (1.32)   
test_benchmark_single_insert[redis_store-book1]                 312.5839 (2.54)     279.5660 (2.56)       578.7070 (1.39)   
test_benchmark_single_insert[redis_store-book3]                 316.9207 (2.58)     284.8630 (2.60)       567.0120 (1.36)   
test_benchmark_select_columns[redis_store]                      369.1538 (3.00)     331.5770 (3.03)       666.0470 (1.60)   
test_benchmark_select_default[redis_store]                      553.9420 (4.51)     485.3700 (4.44)     1,235.8540 (2.96)   
test_benchmark_bulk_insert[redis_store]                         777.4058 (6.32)     730.4280 (6.68)     1,012.7780 (2.43)   
----------------------------------------------------------------------------------------------------------------------------

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
