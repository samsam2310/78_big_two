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
        handleTrow: function(){
            ;
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
            var start_btn = null;
            var that = this;
            if(this.props.start_btn){
                start_btn = (<button
                    onClick={function(){that.props.onClick({'type':'start'})}}>開始</button>);
            }
            return (
                <div>
                    <h4>{this.props.name}</h4>
                    <div>{ch_c}</div>
                    <div>{card}</div>
                    <div>
                        {start_btn}
                        <button onClick={function(){that.handleTrow}}>出牌</button>
                        <button onClick={function(){that.props.onClick({'type':'pick'})}}>抽牌</button>
                    </div>
                </div>
            );
        }
    });
    var GameTable = React.createClass({
        getInitialState: function() {
            return {
                status: '?',
                your_name: 'Name',
                your_card: ['0A','4K'],
                current_card: ['3K','2K'],
                players: [{name: 'a', card: 2},{name: 'b', card: 2}],
                room_manager: 'Manager',
                online_user: 0,
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
        handleClick: function(cli) {
            if(cli.type=='start'){
                this.send({'req': 'start'});
            }else if(cli.type=='throw'){
                console.log('throw');
            }else if(cli.type=='pick'){
                console.log('pick');
            }
        },
        render: function() {
            var players = this.state.players.map(function(v){
                return (<div>Name: {v['name']}, card: {v['card']}, conn: {Number(v['conn'])}</div>);
            });
            return (<div>
                <div>Online: {this.state.online_user}</div>
                <div>Status: {this.state.status}</div>
                <Table cards={this.state.current_card}/>
                {players}
                <Player name={this.state.your_name}
                    cards={this.state.your_card}
                    start_btn={this.state.your_name==this.state.room_manager && this.state.status=='init'}
                    onClick={this.handleClick}/>
            </div>);
        }
    });
    ReactDOM.render(
        <GameTable />,
        document.getElementById('groot')
    );
    console.log('init-end');
}())
