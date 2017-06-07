#include <zmq.hpp>
#include <sstream>
#include <iostream>

int main ()
{
	int port = 5556;

	std::ostringstream oss;
	oss << "tcp://172.18.0.1:" << port;

	zmq::context_t ctx(1);
	zmq::socket_t s(ctx, ZMQ_PAIR);
	s.connect(oss.str().c_str());

	zmq::message_t handshake (5);
	memcpy(handshake.data(), "hello", 5);
	s.send(handshake);

	zmq::message_t env_reward, env_input;
	s.recv(&env_reward);
	s.recv(&env_input);

	while(true) {
		zmq::message_t action(1);
		memcpy(action.data(), "a", 1); // Replace "a" with your answer.

		s.send(action);
		s.recv(&env_reward);
		s.recv(&env_input);

		std::string parsed_reward((char*)env_reward.data(), env_reward.size());
		// parsed_reward contains "0", "-1" or "1".

		std::cout << parsed_reward << std::endl;
	}
}

