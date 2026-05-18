{{ config(materialized='view') }}

select
    order_id
    , merchant_id
    , customer_id
    , order_status
    , is_test
    , cast(ordered_at as timestamp) as ordered_at
    , cast(paid_at as timestamp) as paid_at
from {{ ref('base_orders') }}
