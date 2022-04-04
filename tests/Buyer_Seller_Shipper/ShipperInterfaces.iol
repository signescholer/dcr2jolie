interface Seller1ShipperInterface{
	oneWay:
		order1(string)
}

interface Seller2ShipperInterface{
	oneWay:
		order2(string)
}

interface ShipperBuyerInterface{
	oneWay:
		details(string)
}

