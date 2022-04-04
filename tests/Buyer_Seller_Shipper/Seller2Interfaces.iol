interface BuyerSeller2Interface{
	oneWay:
		ask(string),
		accept2(void),
		accept1(void),
		reject(void)
}

interface Seller2ShipperInterface{
	oneWay:
		order2(string)
}

interface Seller2BuyerInterface{
	oneWay:
		quote2(int)
}

