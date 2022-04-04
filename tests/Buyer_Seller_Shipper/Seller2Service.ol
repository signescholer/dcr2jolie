include "Seller2Interfaces.iol"
include "console.iol"

service Seller2Service{
	execution: single

	inputPort inBuyerService {
		location: "socket://localhost:9001"
		protocol: http { format = "json"}
		interfaces: BuyerSeller2Interface
	}

	outputPort outShipperService {
		location: "socket://localhost:9007"
		protocol: http { format = "json"}
		interfaces: Seller2ShipperInterface
	}

	outputPort outBuyerService {
		location: "socket://localhost:9000"
		protocol: http { format = "json"}
		interfaces: Seller2BuyerInterface
	}


	main {
          [ask(product)]{
               price = 19;
               name = "Seller2"
               invoice.product = product;
               invoice.price = price;
               invoice.seller = name;
               quote2@outBuyerService(price);
               println@Console("Quoted buyer " + invoice.price + "DKK for " + invoice.product + ".")();

               [accept2()]{
                    order2@outShipperService("Order of " + product + "to Buyer, from "+name+".");
                    println@Console("The price was accepted.")()
               }

               [reject()]{
                    println@Console("The price was rejected.")()
               }
          }
	}
}