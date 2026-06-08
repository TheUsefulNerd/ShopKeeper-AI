import enum


class AgentName(enum.Enum):
    sales = "sales"
    recommendation = "recommendation"
    inventory = "inventory"
    payment = "payment"
    fulfillment = "fulfillment"
    loyalty_offers = "loyalty_offers"
    supplier = "supplier"
    customer_generator = "customer_generator"
    post_purchase = "post_purchase"
