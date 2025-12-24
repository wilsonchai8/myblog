package main

import (
	"log"
	"net"

	corepb "github.com/envoyproxy/go-control-plane/envoy/config/core/v3"
	endpointpb "github.com/envoyproxy/go-control-plane/envoy/config/endpoint/v3"
	discoverypb "github.com/envoyproxy/go-control-plane/envoy/service/discovery/v3"

	"google.golang.org/grpc"
	"google.golang.org/protobuf/types/known/anypb"
)

type adsServer struct {
	discoverypb.UnimplementedAggregatedDiscoveryServiceServer
}

func main() {
	lis, err := net.Listen("tcp", ":18000")
	if err != nil {
		log.Fatalf("listen failed: %v", err)
	}

	grpcServer := grpc.NewServer()
	discoverypb.RegisterAggregatedDiscoveryServiceServer(
		grpcServer,
		&adsServer{},
	)

	log.Println("ADS (EDS only) server listening on :18000")
	if err := grpcServer.Serve(lis); err != nil {
		log.Fatalf("grpc serve failed: %v", err)
	}
}

func (s *adsServer) StreamAggregatedResources(
	stream discoverypb.AggregatedDiscoveryService_StreamAggregatedResourcesServer,
) error {

	log.Println("Envoy connected to ADS")

	for {
		req, err := stream.Recv()
		if err != nil {
			return err
		}

		log.Printf(
			"DiscoveryRequest type=%s resources=%v node=%s",
			req.TypeUrl,
			req.ResourceNames,
			req.Node.Id,
		)

		log.Printf(req.TypeUrl)
		if req.TypeUrl != "type.googleapis.com/envoy.config.endpoint.v3.ClusterLoadAssignment" {
			continue
		}

		cla := buildClusterLoadAssignment()
		anyRes, err := anypb.New(cla)
		if err != nil {
			return err
		}

		resp := &discoverypb.DiscoveryResponse{
			VersionInfo: "v1",
			TypeUrl:     req.TypeUrl,
			Resources:   []*anypb.Any{anyRes},
			Nonce:       "1",
		}

		if err := stream.Send(resp); err != nil {
			return err
		}
	}
}

func buildClusterLoadAssignment() *endpointpb.ClusterLoadAssignment {
	return &endpointpb.ClusterLoadAssignment{
		ClusterName: "backend_cluster",
		Endpoints: []*endpointpb.LocalityLbEndpoints{
			{
				LbEndpoints: []*endpointpb.LbEndpoint{
					buildLbEndpoint("10.244.0.82", 10000),
					buildLbEndpoint("10.244.0.81", 10000),
				},
			},
		},
	}
}

func buildLbEndpoint(ip string, port uint32) *endpointpb.LbEndpoint {
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
