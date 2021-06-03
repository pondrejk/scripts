import React from 'react';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import { connect } from 'react-redux';

const mapStateToProps = (state) => {
  return {
    stateItem: state.stateItem,
  };
};

class App extends React.Component {
  render() {
    return (
      <Container fluid>
        <Row>
          <Col xs={12}>
            <h1>Hello World</h1>
          </Col>
        </Row>
      </Container>
    );
  }
}

App = connect(mapStateToProps)(App);
export default App;
