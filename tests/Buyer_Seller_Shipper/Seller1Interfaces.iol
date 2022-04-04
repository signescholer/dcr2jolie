interface BuyerSeller1Interface{
	oneWay:
		reject(void),
		accept2(void),
		ask(string),
		accept1(void)
}

interface Seller1ShipperInterface{
	oneWay:
		order1(string)
}

interface Seller1BuyerInterface{
	oneWay:
		quote1(int)
}

