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
