#!/usr/bin/env python

import cmd_parser
from graph import DCRChoreography

def main():
    """ #modified heavily. """
    verbatim = False #Should be a run option.

    global dcr_choreography
    try:
        dcr_choreography = DCRChoreography().from_xml(xml_path)
    except ValueError as e:
        print("Interfaces could not be made.")
        print("ErrorMessage:",e)
        return
    except FileNotFoundError:
        print("Input file not found. Some example files can be found in the folder 'input'.")
        return

    if verbatim:
        print("GRAPH:",dcr_choreography,"\n")
        print("Users: ",dcr_choreography.get_users())
        print("Services: ",dcr_choreography.get_services())
        print("Actions: ",[e.ActivityName+("("+e.datatype+")" if not e.isNest else "") for e in dcr_choreography.Nodes],"\n")

    #Alright! Now we've got the instance!

    try:
        projections = {}
        for a in dcr_choreography.get_roles():
                projections[a] = dcr_choreography.project_for_actor(a)
    except AssertionError:
        print("Interfaces could not be made, as the graph is not projectable.")
        return

        
    for a,p in projections.items():
        if verbatim:
            print("\n\nProjection for ",a,":",p.get_roles(),"\n",p)
            print("Included,",[e.ActivityName for e in p.InitialIncluded])
            print("Excluded",[e.ActivityName for e in p.Nodes if e not in p.InitialIncluded])
            print("Pending,",[e.ActivityName for e in p.InitialPending])
            print("Executed,",[e.ActivityName for e in p.InitialExecuted])

        p.generate_jolie("/output")
    print("Interface files can be found in the folder 'output'.")

if __name__ == '__main__':
    # input parameters
    args = cmd_parser.parse_args()
    xml_path = args.xml
    main()
