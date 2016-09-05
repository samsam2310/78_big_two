(function(){
    console.log('init');
    var Table = React.createClass({
        render: function() {
            var cards = this.props.cards.map(function(v){
                return (<span>{v}</span>);
            });
            return (<div>{cards}</div>);
        }
    });
    var Player = React.createClass({
        getInitialState: function() {
            return {
                status: []
            };
        },
        componentWillReceiveProps: function(nxtProp) {
            if(nxtProp.cards)this.setState({status: []});
        },
        render: function() {
            var that = this;
            var ch_c = this.props.cards.map(function(v, i){
                if(that.state.status[i]){
                    return (<span>{v}</span>);
                }
                return (<span/>);
            });
            var card = this.props.cards.map(function(v, i){
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
                your_card: ['0A','4K'],
                current_card: ['3K','2K'],
                players: [{name: 'a', card: 2},{name: 'b', card: 2}]
            };
        },
        componentDidMount: function() {
            var url = 'ws://' + window.location.host + '/gamesocket'
            var conn = new WebSocket(url);
            this.send = function(json) {
                conn.send(JSON.stringify(json));
            };
            var that = this;
            conn.onmessage = function(evt) {
                var json = JSON.parse(evt.data);
                that.handleMessage(json);
            };
        },
        handleMessage: function(json) {
            if(json.$set){
                console.log("Set!!!");
                console.log(json);
                this.setState(json.$set);
            }
        },
        render: function() {
            var players = this.state.players.map(function(v){
                return (<div>Name: {v['name']}, card: {v['card']}</div>);
            });
            return (<div>
                <Table cards={this.state.current_card}/>
                {players}
                <Player name={'GG'} cards={this.state.your_card} />
            </div>);
        }
    });
    ReactDOM.render(
        <GameTable />,
        document.getElementById('groot')
    );
    console.log('init-end');
}())
