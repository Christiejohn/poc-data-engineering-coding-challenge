{{ config(materialized='view') }}

SELECT
    order_id
    , merchant_id
    , customer_id
    , order_status
    , is_test
    , CAST(ordered_at AS timestamp) AS ordered_at
    , CAST(paid_at AS timestamp) AS paid_at
FROM {{ ref('base_orders') }}
