{% docs order_fact_revenue %}
Revenue per order in dollars. Defined as the sum of `quantity * unit_price` across
the order's line items, **gross of refunds, no tax, no shipping, no discounts**.
Refunds are loaded separately and not subtracted here.
{% enddocs %}
