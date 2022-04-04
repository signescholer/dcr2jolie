include "BuyerInterfaces.iol"
include "console.iol"

service BuyerService{
	execution: single

	inputPort inShipperService {
		location: "socket://localhost:9003"
		protocol: http { format = "json"}
		interfaces: ShipperBuyerInterface
	}

	inputPort inSeller2Service {
		location: "socket://localhost:9000"
		protocol: http { format = "json"}
		interfaces: Seller2BuyerInterface
	}

	inputPort inSeller1Service {
		location: "socket://localhost:9004"
		protocol: http { format = "json"}
		interfaces: Seller1BuyerInterface
	}

	outputPort outSeller2Service {
		location: "socket://localhost:9001"
		protocol: http { format = "json"}
		interfaces: BuyerSeller2Interface
	}

	outputPort outSeller1Service {
		location: "socket://localhost:9005"
		protocol: http { format = "json"}
		interfaces: BuyerSeller1Interface
	}


	main {
      ask@outSeller1Service("chips")
      {
        [quote1(price1)]
      }
      ask@outSeller2Service("chips")
      {
        [quote2(price2)]
      }
    maxprice = 18;
    accepted = true;
    if(price1 <= price2 && price1 < maxprice){
      accept1@outSeller1Service();
      reject@outSeller2Service();
      println@Console("Accepted "+price1+" from Seller1, rejected "+price2+" from Seller2.")()
    }else if(price2 < maxprice){
      accept2@outSeller2Service();
      reject@outSeller1Service();
      println@Console("Accepted "+price2+" from Seller2, rejected "+price1+" from Seller1.")()
    }else{
      reject@outSeller1Service();
      reject@outSeller2Service();
      println@Console("Rejected both "+price1+" and "+price2+" from Seller2 and Seller2, respectively.")()
      accepted = false
    }
    if(accepted){
      [details(invoice)]{
        println@Console("Received the invoice from Shipper: "+invoice)()
      }
    }

	}
}