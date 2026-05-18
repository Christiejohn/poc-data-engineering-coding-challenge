{{ config(materialized='view') }}

SELECT *
FROM {{ source('raw', 'line_items') }}
