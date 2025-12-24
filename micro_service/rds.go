package main

import (
	"fmt"
	"log"
	"net"
	"time"

	routepb "github.com/envoyproxy/go-control-plane/envoy/config/route/v3"

	discoverypb "github.com/envoyproxy/go-control-plane/envoy/service/discovery/v3"
	rdsservice "github.com/envoyproxy/go-control-plane/envoy/service/route/v3"

	"google.golang.org/grpc"
	"google.golang.org/protobuf/types/known/anypb"
)

type RDSServer struct {
	rdsservice.UnimplementedRouteDiscoveryServiceServer

	version   int64
	routeName string
	streams   map[rdsservice.RouteDiscoveryService_StreamRoutesServer]string
}

func NewRDSServer() *RDSServer {
	return &RDSServer{
		version:   time.Now().UnixNano(),
		routeName: "local_route",
		streams:   make(map[rdsservice.RouteDiscoveryService_StreamRoutesServer]string),
	}
}

func (s *RDSServer) StreamRoutes(
	stream rdsservice.RouteDiscoveryService_StreamRoutesServer,
) error {
	log.Println("RDS stream connected")

	defer func() {
		delete(s.streams, stream)
		log.Println("RDS stream disconnected")
	}()

	if err := s.send(stream, ""); err != nil {
		log.Printf("Initial send failed: %v", err)
		return err
	}

	for {
		req, err := stream.Recv()
		if err != nil {
			log.Printf("Stream recv error: %v", err)
			return err
		}

		if len(req.ResourceNames) > 0 {
			s.streams[stream] = req.ResourceNames[0]
		}

		log.Printf(
			"DiscoveryRequest resources=%v version=%q nonce=%q",
			req.ResourceNames,
			req.VersionInfo,
			req.ResponseNonce,
		)
	}
}

func (s *RDSServer) send(
	stream rdsservice.RouteDiscoveryService_StreamRoutesServer,
	responseNonce string,
) error {
	resp, err := s.buildResponse(responseNonce)
	if err != nil {
		return err
	}

	log.Printf(">>> Sending RDS response version=%s, nonce=%s",
		resp.VersionInfo, resp.Nonce)

	return stream.Send(resp)
}

func (s *RDSServer) buildResponse(responseNonce string) (*discoverypb.DiscoveryResponse, error) {
	routeConfig := &routepb.RouteConfiguration{
		Name: s.routeName,
		VirtualHosts: []*routepb.VirtualHost{
			{
				Name:    "backend_service",
				Domains: []string{"*"},
				Routes: []*routepb.Route{
					{
						Match: &routepb.RouteMatch{
							PathSpecifier: &routepb.RouteMatch_Prefix{
								Prefix: "/test",
							},
						},
						Action: &routepb.Route_Route{
							Route: &routepb.RouteAction{
								ClusterSpecifier: &routepb.RouteAction_Cluster{
									Cluster: "backend_cluster",
								},
							},
						},
					},
				},
			},
		},
	}

	anyRes, err := anypb.New(routeConfig)
	if err != nil {
		return nil, err
	}

	nonce := fmt.Sprintf("%d", time.Now().UnixNano())
	if responseNonce != "" {
		nonce = responseNonce + "-" + nonce
	}

	return &discoverypb.DiscoveryResponse{
		VersionInfo: fmt.Sprintf("%d", s.version),
		TypeUrl:     "type.googleapis.com/envoy.config.route.v3.RouteConfiguration",
		Resources:   []*anypb.Any{anyRes},
		Nonce:       nonce,
	}, nil
}

func main() {
	lis, err := net.Listen("tcp", ":18001")
	if err != nil {
		log.Fatalf("listen failed: %v", err)
	}

	grpcServer := grpc.NewServer()
	rds := NewRDSServer()

	rdsservice.RegisterRouteDiscoveryServiceServer(grpcServer, rds)

	log.Println("RDS server listening on :18001")
	if err := grpcServer.Serve(lis); err != nil {
		log.Fatal(err)
	}
}
