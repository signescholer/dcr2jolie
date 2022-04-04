include "Seller1Interfaces.iol"
include "console.iol"

service Seller1Service{
	execution: single

	inputPort inBuyerService {
		location: "socket://localhost:9005"
		protocol: http { format = "json"}
		interfaces: BuyerSeller1Interface
	}

	outputPort outShipperService {
		location: "socket://localhost:9006"
		protocol: http { format = "json"}
		interfaces: Seller1ShipperInterface
	}

	outputPort outBuyerService {
		location: "socket://localhost:9004"
		protocol: http { format = "json"}
		interfaces: Seller1BuyerInterface
	}


	main {
          [ask(product)]{
               price = 16;
               name = "Seller1"
               invoice.product = product;
               invoice.price = price;
               invoice.seller = name;
               quote1@outBuyerService(price);
               println@Console("Quoted buyer " + invoice.price + "DKK for " + invoice.product + ".")();

               [accept1()]{
                    order1@outShipperService("Order of " + product + "to Buyer, from "+name+".");
                    println@Console("The price was accepted.")()
               }

               [reject()]{
                    println@Console("The price was rejected.")()
               }
          }
	}
}