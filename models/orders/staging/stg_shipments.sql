{{ config(materialized='view') }}

SELECT
    shipment_id
    , order_id
    , CAST(shipped_at AS timestamp) AS shipped_at
FROM {{ ref('base_shipments') }}
