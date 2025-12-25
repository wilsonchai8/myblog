package main

import (
	"fmt"
	"log"
	"net"
	"time"

	corepb "github.com/envoyproxy/go-control-plane/envoy/config/core/v3"
	endpointpb "github.com/envoyproxy/go-control-plane/envoy/config/endpoint/v3"
	routepb "github.com/envoyproxy/go-control-plane/envoy/config/route/v3"

	adsservice "github.com/envoyproxy/go-control-plane/envoy/service/discovery/v3"
	discoverypb "github.com/envoyproxy/go-control-plane/envoy/service/discovery/v3"

	"google.golang.org/grpc"
	"google.golang.org/protobuf/types/known/anypb"
)

type ADSServer struct {
	adsservice.UnimplementedAggregatedDiscoveryServiceServer

	version     int64
	clusterName string
	routeName   string

	endpoints []*endpointpb.LbEndpoint
}

func NewADSServer() *ADSServer {
	return &ADSServer{
		version:     time.Now().UnixNano(),
		clusterName: "backend_cluster",
		routeName:   "local_route",
		endpoints: []*endpointpb.LbEndpoint{
			newEndpoint("10.244.0.111", 10000),
			newEndpoint("10.244.0.114", 10000),
		},
	}
}

func (s *ADSServer) StreamAggregatedResources(
	stream adsservice.AggregatedDiscoveryService_StreamAggregatedResourcesServer,
) error {
	log.Println("ADS stream connected")

	for {
		req, err := stream.Recv()
		if err != nil {
			log.Printf("ADS stream recv error: %v", err)
			return err
		}

		switch req.TypeUrl {
		case "type.googleapis.com/envoy.config.endpoint.v3.ClusterLoadAssignment":
			if err := s.sendEDS(stream, req.ResponseNonce); err != nil {
				return err
			}

		case "type.googleapis.com/envoy.config.route.v3.RouteConfiguration":
			if err := s.sendRDS(stream, req.ResponseNonce); err != nil {
				return err
			}

		default:
			log.Printf("Ignore typeUrl: %s", req.TypeUrl)
		}
	}
}

func (s *ADSServer) sendEDS(
	stream adsservice.AggregatedDiscoveryService_StreamAggregatedResourcesServer,
	responseNonce string,
) error {
	cla := &endpointpb.ClusterLoadAssignment{
		ClusterName: s.clusterName,
		Endpoints: []*endpointpb.LocalityLbEndpoints{
			{
				LbEndpoints: s.endpoints,
			},
		},
	}

	anyRes, _ := anypb.New(cla)

	return stream.Send(&discoverypb.DiscoveryResponse{
		VersionInfo: fmt.Sprintf("%d", s.version),
		TypeUrl:     "type.googleapis.com/envoy.config.endpoint.v3.ClusterLoadAssignment",
		Resources:   []*anypb.Any{anyRes},
		Nonce:       nextNonce(responseNonce),
	})
}

func (s *ADSServer) sendRDS(
	stream adsservice.AggregatedDiscoveryService_StreamAggregatedResourcesServer,
	responseNonce string,
) error {
	rc := &routepb.RouteConfiguration{
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
									Cluster: s.clusterName,
								},
							},
						},
					},
				},
			},
		},
	}

	anyRes, _ := anypb.New(rc)

	return stream.Send(&discoverypb.DiscoveryResponse{
		VersionInfo: fmt.Sprintf("%d", s.version),
		TypeUrl:     "type.googleapis.com/envoy.config.route.v3.RouteConfiguration",
		Resources:   []*anypb.Any{anyRes},
		Nonce:       nextNonce(responseNonce),
	})
}

func nextNonce(prev string) string {
	n := fmt.Sprintf("%d", time.Now().UnixNano())
	if prev != "" {
		return prev + "-" + n
	}
	return n
}

func newEndpoint(ip string, port uint32) *endpointpb.LbEndpoint {
	return &endpointpb.LbEndpoint{
		HostIdentifier: &endpointpb.LbEndpoint_Endpoint{
			Endpoint: &endpointpb.Endpoint{
				Address: &corepb.Address{
					Address: &corepb.Address_SocketAddress{
						SocketAddress: &corepb.SocketAddress{
							Protocol: corepb.SocketAddress_TCP,
							Address:  ip,
							PortSpecifier: &corepb.SocketAddress_PortValue{
								PortValue: port,
							},
						},
					},
				},
			},
		},
	}
}

func main() {
	lis, err := net.Listen("tcp", ":18000")
	if err != nil {
		log.Fatal(err)
	}

	grpcServer := grpc.NewServer()
	ads := NewADSServer()

	adsservice.RegisterAggregatedDiscoveryServiceServer(grpcServer, ads)

	log.Println("ADS server listening on :18000")
	log.Fatal(grpcServer.Serve(lis))
}
