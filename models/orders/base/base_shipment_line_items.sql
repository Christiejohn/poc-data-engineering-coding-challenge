{{ config(materialized='view') }}

SELECT *
FROM {{ source('raw', 'shipment_line_items') }}
