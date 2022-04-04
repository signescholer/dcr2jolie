include "ShipperInterfaces.iol"
include "console.iol"

service ShipperService{
	execution: sequential

	inputPort inSeller2Service {
		location: "socket://localhost:9007"
		protocol: http { format = "json"}
		interfaces: Seller2ShipperInterface
	}

	inputPort inSeller1Service {
		location: "socket://localhost:9006"
		protocol: http { format = "json"}
		interfaces: Seller1ShipperInterface
	}

	outputPort outBuyerService {
		location: "socket://localhost:9003"
		protocol: http { format = "json"}
		interfaces: ShipperBuyerInterface
	}


	main {
      [order1(invoice)]{
        details@outBuyerService("Details: "+invoice)
        println@Console("Invoice sent to buyer: "+invoice)()
      }

	  [order2(invoice)]{
        details@outBuyerService("Details:"+invoice)
        println@Console("Invoice sent to buyer: "+invoice)()
      }
	}
}