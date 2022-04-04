interface ShipperBuyerInterface{
	oneWay:
		details(string)
}

interface Seller1BuyerInterface{
	oneWay:
		quote1(int)
}

interface Seller2BuyerInterface{
	oneWay:
		quote2(int)
}

interface BuyerSeller2Interface{
	oneWay:
		reject(void),
		ask(string),
		accept1(void),
		accept2(void)
}

interface BuyerSeller1Interface{
	oneWay:
		reject(void),
		ask(string),
		accept1(void),
		accept2(void)
}

