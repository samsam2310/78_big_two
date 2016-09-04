(function(){
    console.log('init');
    var Player = React.createClass({
        getInitialState: function() {
            return {
                card: ['0A','3K'],
                status: [false, false]
            };
        },
        render: function() {
            var that = this;
            var ch_c = this.state.card.map(function(v, i){
                if(that.state.status[i]){
                    return (<span>{v}</span>);
                }
                return (<span/>);
            });
            var card = this.state.card.map(function(v, i){
                var click = function(){
                    var status = that.state.status.slice();
                    status[i] = !status[i];
                    that.setState({status: status});
                }
                return (<button onClick={click}>{v}</button>);
            });
            return (
                <div>
                    <h4>{this.props.name}</h4>
                    <div>{ch_c}</div>
                    <div>{card}</div>
                </div>
            );
        }
    });
    var GameTable = React.createClass({
        getInitialState: function() {
            return {
                players: ['a','b']
            };
        },
        render: function() {
            var players = this.state.players.map(function(v){
                return (<Player name={v} />);
            });
            return (
                <div>{players}</div>
            );
        }
    });
    ReactDOM.render(
        <GameTable />,
        document.getElementById('groot')
    );
    console.log('init-end');
}())
